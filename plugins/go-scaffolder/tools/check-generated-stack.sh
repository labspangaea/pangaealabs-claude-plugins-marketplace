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
# api-* combos only. A generated consumer/publisher compose file cannot come up
# at all today: the template emits no broker service, leaves the broker env at
# its localhost default, and healthchecks /healthz against a process that
# serves no HTTP. Verified — publisher-redis-nodb-none dials 127.0.0.1:6379 and
# the container exits. Fixing that is a template change, not something this
# check can absorb, so non-api combos are refused with a pointer rather than
# left to fail confusingly.
#
#   ./check-generated-stack.sh [combo-id]
#
set -euo pipefail

COMBO="${1:-api-chi-mysql-couchbase}"

case "$COMBO" in
  api-*) ;;
  *)
    echo "  [skip] $COMBO — generated consumer/publisher compose files emit no" >&2
    echo "         broker service and healthcheck an HTTP endpoint that does not" >&2
    echo "         exist. api-* combos only until the template is fixed." >&2
    exit 0
    ;;
esac
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
# healthy, which includes the app's own /healthz and therefore proves it
# connected to its database and cache.
echo "==> docker compose up -d --wait"
(cd "$WORK" && docker compose up -d --wait --quiet-pull) || fail "stack did not come up healthy"

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
