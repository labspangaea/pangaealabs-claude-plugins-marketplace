#!/usr/bin/env bash
#
# Boots a generated scaffold's OWN docker-compose.yml and proves the service
# reaches its dependencies.
#
# This is the gap that let a broken couchbase service sit in the templates
# indefinitely: the compile matrix only runs `go build`, and the runtime suite
# starts binaries directly against the maintainer compose stack. Neither one
# ever rendered docker-compose.yml.tmpl and brought it up, so a compose file
# that could not work rendered green forever.
#
# Covers every combo type. api scaffolds are proved by CRUD through their own
# HTTP surface; consumer and publisher scaffolds serve no HTTP at all, so they
# are proved by staying up and by asking the BROKER who attached.
#
#   ./check-generated-stack.sh [combo-id]
#
set -euo pipefail

COMBO="${1:-api-chi-mysql-couchbase}"
SMOKE="$(cd "$(dirname "${BASH_SOURCE[0]}")/smoke" && pwd)"
WORK="$(mktemp -d)"
PORT=8080

cleanup() {
  local rc=$?
  if [[ -f "$WORK/docker-compose.yml" ]]; then
    # Only on failure — on a pass these logs are hundreds of lines of noise
    # that bury the one line anyone reads.
    [[ $rc -ne 0 ]] && (cd "$WORK" && docker compose logs --tail=40 2>&1 | tail -40) || true
    (cd "$WORK" && docker compose down -v >/dev/null 2>&1) || true
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

fail() { printf '  [FAIL] %s\n' "$*" >&2; exit 1; }

echo "==> rendering $COMBO"
(cd "$SMOKE" && go run . -render "$COMBO" -outdir "$WORK") >/dev/null \
  || fail "render"

[[ -f "$WORK/docker-compose.yml" ]] || fail "no docker-compose.yml in the scaffold"

# The Dockerfile COPYs go.sum, which -render does not produce. Every documented
# path to running a scaffold starts with `go mod tidy`, so do that rather than
# teaching the Dockerfile to cope without it.
echo "==> go mod tidy"
(cd "$WORK" && GOWORK=off go mod tidy) >/dev/null 2>&1 || fail "go mod tidy"

echo "==> docker compose config"
(cd "$WORK" && docker compose config) >/dev/null || fail "generated compose file is not valid"

# --wait is the assertion: it returns non-zero unless every service reaches
# healthy, which for an api scaffold includes its own /healthz and therefore
# proves it connected to its database and cache.
#
# Bounded, because `--wait` does not terminate on its own when the app crash
# loops under `restart: on-failure` — it keeps seeing a container that is
# briefly running and never concludes. Unbounded, a broken scaffold burns the
# whole CI job timeout and reports nothing useful. 7 minutes is well clear of
# the slowest real case (couchbase cold-pulls and initialises in ~2).
echo "==> docker compose up -d --wait"
if ! (cd "$WORK" && timeout 420 docker compose up -d --wait --quiet-pull); then
  rc=$?
  [[ $rc -eq 124 ]] && fail "stack did not converge within 7m — app is probably crash looping"
  fail "stack did not come up healthy"
fi

# --- consumer / publisher --------------------------------------------------
# These serve no HTTP, so there is no endpoint to poll and (by design) no
# healthcheck on the app service. Two assertions instead.
if [[ "$COMBO" != api-* ]]; then
  app=$(cd "$WORK" && docker compose ps -q "smoke-$COMBO")
  [[ -n "$app" ]] || fail "no app container for $COMBO"

  # 1. It is still alive after a settle window. A scaffold that cannot reach
  #    its broker exits — that is exactly how the missing-broker-service bug
  #    presented — and `restart: on-failure` would otherwise hide it behind a
  #    crash loop that looks momentarily running.
  echo "==> app stays up"
  sleep 10
  running=$(docker inspect -f '{{.State.Running}}' "$app")
  restarts=$(docker inspect -f '{{.RestartCount}}' "$app")
  [[ "$running" == "true" ]] || fail "app container is not running (exited $(docker inspect -f '{{.State.ExitCode}}' "$app"))"
  [[ "$restarts" == "0" ]] || fail "app container restarted $restarts times — crash loop"

  # 2. The broker agrees something attached. "No error in the log" is not
  #    evidence: publishers log nothing at all on success, so silence is
  #    indistinguishable between working and never-started.
  broker_svc() { (cd "$WORK" && docker compose ps -q "$1"); }
  proof="attaches to its broker"

  if [[ "$COMBO" == *-kafka-* ]]; then
    k=$(broker_svc kafka); [[ -n "$k" ]] || fail "no kafka container"
    if [[ "$COMBO" == consumer-* ]]; then
      echo "==> kafka consumer group registered"
      groups=$(docker exec "$k" /opt/kafka/bin/kafka-consumer-groups.sh \
        --bootstrap-server localhost:9092 --list 2>/dev/null || true)
      grep -q "smoke-$COMBO" <<<"$groups" \
        || fail "consumer group smoke-$COMBO not registered with kafka (got: ${groups:-none})"
    else
      # kafka-go's Writer connects lazily, on first produce. A publisher that
      # has not published yet holds no connection, so there is genuinely
      # nothing broker-side to observe — the liveness check above is the
      # assertion. Stated rather than silently skipped.
      echo "==> kafka publisher: no broker-side check (writer connects lazily)"
      proof="stays up (kafka writer connects lazily — nothing to observe yet)"
    fi

  elif [[ "$COMBO" == *-rabbitmq-* ]]; then
    r=$(broker_svc rabbitmq); [[ -n "$r" ]] || fail "no rabbitmq container"
    echo "==> rabbitmq connection from the app"
    conns=$(docker exec "$r" rabbitmqctl -q list_connections name 2>/dev/null | grep -c . || true)
    [[ "${conns:-0}" -ge 1 ]] || fail "rabbitmq reports no client connections — app never attached"

  elif [[ "$COMBO" == *-redis-* ]]; then
    rd=$(broker_svc redis); [[ -n "$rd" ]] || fail "no redis container"
    topic=$(grep '^KAFKA_TOPIC=' "$WORK/.env" | cut -d= -f2-)
    [[ -n "$topic" ]] || fail "no KAFKA_TOPIC in .env — consumer would subscribe to nothing"

    # redis is the one broker where queue and pubsub are genuinely different
    # mechanisms, so assert the one this combo asked for. kafka and rabbitmq
    # are competing-consumer either way, which is why only redis splits here.
    #
    # This is worth asserting rather than settling for "a client connected":
    # a scaffold quietly using Pub/Sub in queue mode would look identical by
    # connection count while losing the delivery guarantee it promised. The
    # docs made exactly that mistake before — redis was described as Streams
    # when it was Pub/Sub.
    if [[ "$COMBO" == consumer-* ]]; then
      if [[ "$COMBO" == *-queue ]]; then
        echo "==> redis Streams consumer group on $topic"
        groups=$(docker exec "$rd" redis-cli XINFO GROUPS "$topic" 2>/dev/null || true)
        grep -q "smoke-$COMBO" <<<"$groups" \
          || fail "no Streams consumer group smoke-$COMBO on '$topic' — queue mode is not using Streams"
        proof="registers a Streams consumer group on $topic"
      else
        echo "==> redis Pub/Sub subscription to $topic"
        chans=$(docker exec "$rd" redis-cli PUBSUB CHANNELS 2>/dev/null || true)
        grep -qx "$topic" <<<"$chans" \
          || fail "not subscribed to Pub/Sub channel '$topic' (got: ${chans:-none})"
        proof="subscribes to Pub/Sub channel $topic"
      fi
    else
      # A publisher neither subscribes nor creates a group, so connection
      # count is all there is — and it is still falsifiable: without the app
      # only redis-cli is connected.
      echo "==> redis connection from the app"
      clients=$(docker exec "$rd" redis-cli INFO clients 2>/dev/null \
        | grep -oP 'connected_clients:\K[0-9]+' || echo 0)
      [[ "${clients:-0}" -ge 2 ]] || fail "redis reports $clients client(s) — app never attached"
      proof="attaches to redis (a publisher subscribes to nothing)"
    fi
  fi

  echo "  [pass] $COMBO — generated stack boots and $proof"
  exit 0
fi

# A database=none scaffold has no repository wired, so there is nothing to
# CRUD. Reaching healthy is the whole assertion for it — the compose file
# rendered, built and booted.
if ! grep -q '^DATABASE_DSN=' "$WORK/.env"; then
  curl -sfS "http://localhost:$PORT/healthz" >/dev/null || fail "healthz"
  echo "  [pass] $COMBO — generated stack boots (database=none, no CRUD to run)"
  exit 0
fi

echo "==> CRUD through the generated API"
id=$(curl -sfS -X POST "http://localhost:$PORT/api/v1/orders" \
  -H 'Content-Type: application/json' \
  -d '{"product_code":"SKU-CI","quantity":7,"in_stock":true}' | jq -r '.data.id // empty')
[[ -n "$id" ]] || fail "create returned no id"
curl -sfS "http://localhost:$PORT/api/v1/orders/$id" >/dev/null || fail "find after create"

# Cache assertion for the caches that are observable from outside the process.
# Both read their connection details from the generated .env — the same file
# the service reads — so a compose file that stands a cache up with values the
# service does not use fails here rather than passing against a service nobody
# talks to. That is exactly how the couchbase break survived.
#
# memory is deliberately unasserted: it lives in-process and has nothing to
# look at. cache=none has no cache. Both still have to reach healthy above.
if grep -q '^COUCHBASE_BUCKET=' "$WORK/.env"; then
  bucket=$(grep '^COUCHBASE_BUCKET=' "$WORK/.env" | cut -d= -f2-)
  user=$(grep '^COUCHBASE_USERNAME=' "$WORK/.env" | cut -d= -f2-)
  pass=$(grep '^COUCHBASE_PASSWORD=' "$WORK/.env" | cut -d= -f2-)
  cb=$(cd "$WORK" && docker compose ps -q couchbase)
  [[ -n "$cb" ]] || fail "no couchbase container despite COUCHBASE_BUCKET in .env"

  echo "==> cache document in bucket $bucket"
  status=$(docker exec "$cb" curl -s -o /dev/null -w '%{http_code}' \
    -u "$user:$pass" \
    "http://localhost:8091/pools/default/buckets/$bucket/docs/order%3A$id" 2>/dev/null)
  [[ "$status" == "200" ]] \
    || fail "no cache document order:$id in $bucket (HTTP ${status:-none}) — service is not using its cache"

elif grep -q '^REDIS_ADDR=' "$WORK/.env"; then
  rd=$(cd "$WORK" && docker compose ps -q redis)
  [[ -n "$rd" ]] || fail "no redis container despite REDIS_ADDR in .env"

  echo "==> cache key order:$id in redis"
  # EXISTS rather than a KEYS glob: the key carries a uuid minted by this run,
  # so it cannot be satisfied by anything left over.
  present=$(docker exec "$rd" redis-cli EXISTS "order:$id" 2>/dev/null | tr -d '\r')
  [[ "$present" == "1" ]] \
    || fail "no redis key order:$id — service is not using its cache"
fi

echo "  [pass] $COMBO — generated stack boots and serves"
