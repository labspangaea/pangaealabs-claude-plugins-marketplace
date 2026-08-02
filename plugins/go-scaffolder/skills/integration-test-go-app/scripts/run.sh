#!/usr/bin/env bash
# Integration-test driver for /integration-test-go-app.
#
# For each selected combo:
#   1. Render via `smoke -render` into ./out/<combo>/
#   2. go mod tidy + start `go run ./cmd/<name>` against docker-compose services
#   3. Poll /healthz; on ready, run CRUD + cursor pagination + offset pagination
#      + cache key check + log assertion sequence
#   4. SIGTERM, capture status, move on
#
# Exit 0 if all selected combos pass every assertion; 1 if any combo fails.
#
# Usage:
#   run.sh [filter]       Run all api combos, optionally filter by framework name
#   run.sh nethttp        Just the nethttp combo
#   run.sh --list         List combos that would run, exit
#
# Prerequisites verified at startup:
#   docker, docker compose, jq, curl, go on PATH
#   go-scaffolder docker-compose.yml at the plugin root
# go-lib is a public module — `go mod tidy` (step 2 below) fetches it from the
# public proxy. No token, no GOPRIVATE, no local checkout required.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN="$(cd "$SKILL_DIR/../.." && pwd)"
SMOKE="$PLUGIN/tools/smoke"
COMPOSE_FILE="$PLUGIN/docker-compose.yml"
OUT_BASE="$SKILL_DIR/out"
LOG_BASE="$SKILL_DIR/logs"
PORT=18080

# --- Combo selection -----------------------------------------------------------
# Each entry: combo-id|driver|cache-mode
#   driver: postgres | mysql | bun-postgres | bun-mysql
#   cache-mode: redis | memory | none   (which cache features the runtime tests should expect)
#
# The driver names the ORM as well as the engine because the two differ in DSN
# format — see DSN templates below. bun combos are always cache=none; the cache
# decorator is GORM-typed, so the scaffolder refuses that pairing.
#
# Combos that need services not in docker-compose (couchbase, kafka, rabbitmq) are
# intentionally absent. Add new combos to combos.go + here when those services land.

COMBOS=(
  "api-nethttp-postgres-redis|postgres|redis"
  "api-gin-postgres-memory|postgres|memory"
  "api-mux-postgres-none|postgres|none"
  "api-echo-postgres-redis|postgres|redis"
  "api-nethttp-mysql-none|mysql|none"
  "api-gin-bunpg-none|bun-postgres|none"
  "api-chi-bunmysql-none|bun-mysql|none"
)

# DSN templates — service names match docker-compose service names.
#
# postgres has two forms and they are not interchangeable: GORM's driver takes
# the key=value form, bun's pgdriver only parses the URL form. Handing pgdriver
# the key=value string fails at connect time, not build time, so the mistake
# surfaces as a startup error rather than anything the compiler catches.
#
# mysql needs no split — both ORMs go through go-sql-driver/mysql.
DSN_POSTGRES="host=localhost user=admin password=admin dbname=appdb port=5432 sslmode=disable"
DSN_BUN_POSTGRES="postgres://admin:admin@localhost:5432/appdb?sslmode=disable"
DSN_MYSQL="admin:admin@tcp(localhost:3306)/appdb?parseTime=true&loc=Local"

# engine_of <driver> — strips the ORM half, leaving the database engine.
# Used wherever only the server matters (dropping tables, picking a container).
engine_of() {
  case "$1" in
    postgres | bun-postgres) echo postgres ;;
    mysql | bun-mysql) echo mysql ;;
    *) echo "unknown" ;;
  esac
}

# --- Helpers -------------------------------------------------------------------

log()   { printf '%s\n' "$*"; }
hr()    { printf '%s\n' "----------------------------------------"; }
fail_step() {
  local step="$1" combo="$2" detail="${3:-}"
  printf '  [FAIL] %s — %s\n' "$step" "$combo"
  [[ -n "$detail" ]] && printf '%s\n' "$detail" | sed 's/^/         /'
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "ERROR: required command not found on PATH: $cmd"
    exit 2
  fi
}

# Wait for HTTP healthz; return 0 on ready, 1 on timeout.
wait_healthz() {
  local i
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/healthz" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# kill_pid <pid> — send SIGTERM, wait for exit, fall back to SIGKILL after 5s.
kill_pid() {
  local pid="$1"
  [[ -z "$pid" ]] && return 0
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 5); do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 1
  done
  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

# --- Per-combo runtime test ----------------------------------------------------

# test_api <combo-id> <driver> <cache-mode>
# Returns 0 on full pass, 1 on any failure.
test_api() {
  local combo="$1" driver="$2" cache_mode="$3"
  local out_dir="$OUT_BASE/$combo"
  local log_file="$LOG_BASE/$combo.log"
  local cmd_dir="$out_dir/cmd/smoke-$combo"
  local pid=""

  rm -rf "$out_dir"
  mkdir -p "$LOG_BASE"

  log ""
  hr
  log "==> $combo ($driver, cache=$cache_mode)"
  hr

  # 1. Render
  if ! (cd "$SMOKE" && go run . -render "$combo" -outdir "$out_dir") >/dev/null 2>&1; then
    fail_step "render" "$combo"
    return 1
  fi

  # 2. go mod tidy
  if ! (cd "$out_dir" && GOWORK=off go mod tidy) >>"$log_file" 2>&1; then
    fail_step "go mod tidy" "$combo" "$(tail -10 "$log_file")"
    return 1
  fi

  # 3. Drop existing orders table so each run is reproducible.
  case "$(engine_of "$driver")" in
    postgres)
      docker exec go-scaffolder-postgres psql -U admin -d appdb \
        -c 'DROP TABLE IF EXISTS orders CASCADE;' >/dev/null 2>&1 || true
      ;;
    mysql)
      docker exec go-scaffolder-mysql mysql -uadmin -padmin appdb \
        -e 'DROP TABLE IF EXISTS orders;' >/dev/null 2>&1 || true
      ;;
  esac

  # 4. Build the binary, then run it directly. Using `go run` creates a child
  #    process that doesn't get killed when we send SIGTERM to the wrapper PID,
  #    leaving :8080 occupied for the next combo. Direct binary = our PID is
  #    the actual server.
  if ! (cd "$out_dir" && GOWORK=off go build -o "./bin/svc" "./cmd/smoke-$combo") >>"$log_file" 2>&1; then
    fail_step "go build" "$combo" "$(tail -10 "$log_file")"
    return 1
  fi
  local dsn
  case "$driver" in
    postgres)     dsn="$DSN_POSTGRES" ;;
    bun-postgres) dsn="$DSN_BUN_POSTGRES" ;;
    mysql | bun-mysql) dsn="$DSN_MYSQL" ;;
    *)
      fail_step "dsn" "$combo" "unknown driver: $driver"
      kill_pid "$pid"
      return 1
      ;;
  esac
  # DOCS_ENABLED=true exposes /openapi.{json,yaml} and /docs so we can assert
  # huma's OpenAPI surface in step 11.
  # LOG_BODY=true makes the access log include request_body / response_body
  # fields per request — invaluable when an integration assertion fails and
  # the post-mortem needs the actual wire payload, not just status + duration.
  # SERVICE_BACKEND=real is explicit-on-purpose. The binary is built without
  # `-tags=stub`, so factory_default.go is in play and SERVICE_BACKEND is
  # ignored at runtime — but the .env default is "stub", and if a future
  # change builds the integration binary with `-tags=stub` the unset env
  # would silently route to the canned stub and every CRUD assertion would
  # appear to pass against fake data. Setting it here documents intent and
  # survives that future flip.
  DATABASE_DSN="$dsn" \
  REDIS_ADDR=localhost:6379 REDIS_PASSWORD=admin REDIS_DB=0 \
  HTTP_ADDR=":$PORT" \
  SERVICE_NAME="$combo" \
  SERVICE_BACKEND=real \
  DOCS_ENABLED=true \
  LOG_BODY=true \
  "$out_dir/bin/svc" >>"$log_file" 2>&1 &
  pid=$!

  if ! wait_healthz; then
    fail_step "wait_healthz" "$combo" "$(tail -30 "$log_file")"
    kill_pid "$pid"
    return 1
  fi

  local rc=0

  # 5. CRUD sequence
  local create_resp
  create_resp=$(curl -sfS -X POST "http://localhost:$PORT/api/v1/orders" \
    -H 'Content-Type: application/json' \
    -d '{"product_code":"SKU-001","quantity":42,"in_stock":true}' 2>>"$log_file") || rc=1
  local id
  id=$(echo "$create_resp" | jq -r '.data.id // empty')
  if [[ -z "$id" ]]; then
    fail_step "create" "$combo" "response: $create_resp"
    rc=1
  fi

  if [[ $rc -eq 0 ]]; then
    if ! curl -sfS "http://localhost:$PORT/api/v1/orders/$id" >/dev/null 2>>"$log_file"; then
      fail_step "find" "$combo"; rc=1
    fi

    if ! curl -sfS -X PUT "http://localhost:$PORT/api/v1/orders/$id" \
        -H 'Content-Type: application/json' \
        -d '{"product_code":"SKU-001","quantity":99,"in_stock":false}' >/dev/null 2>>"$log_file"; then
      fail_step "update" "$combo"; rc=1
    fi

    local del_status
    del_status=$(curl -sf -o /dev/null -w '%{http_code}' \
      -X DELETE "http://localhost:$PORT/api/v1/orders/$id" 2>>"$log_file") || true
    if [[ "$del_status" != "204" ]]; then
      fail_step "delete" "$combo" "expected 204, got $del_status"; rc=1
    fi
  fi

  # 6. Seed for pagination tests (25 entities)
  if [[ $rc -eq 0 ]]; then
    for n in $(seq 1 25); do
      curl -sfS -X POST "http://localhost:$PORT/api/v1/orders" \
        -H 'Content-Type: application/json' \
        -d "{\"product_code\":\"SKU-$n\",\"quantity\":$n,\"in_stock\":true}" >/dev/null 2>>"$log_file" \
        || { fail_step "seed-$n" "$combo"; rc=1; break; }
    done
  fi

  # 7. Cursor pagination
  if [[ $rc -eq 0 ]]; then
    local page1 page2 cursor has_next
    page1=$(curl -sfS "http://localhost:$PORT/api/v1/orders?limit=10" 2>>"$log_file") || rc=1
    cursor=$(echo "$page1" | jq -r '.cursor_pagination.next_cursor // empty')
    has_next=$(echo "$page1" | jq -r '.cursor_pagination.has_next')
    if [[ "$has_next" != "true" || -z "$cursor" ]]; then
      fail_step "cursor-page1" "$combo" "has_next=$has_next cursor=$cursor"
      rc=1
    else
      page2=$(curl -sfS "http://localhost:$PORT/api/v1/orders?limit=10&cursor=$cursor" 2>>"$log_file") || rc=1
      local p1_ids p2_ids overlap
      p1_ids=$(echo "$page1" | jq -r '.data[].id' | sort)
      p2_ids=$(echo "$page2" | jq -r '.data[].id' | sort)
      overlap=$(comm -12 <(echo "$p1_ids") <(echo "$p2_ids") | wc -l | tr -d ' ')
      if [[ "$overlap" != "0" ]]; then
        fail_step "cursor-no-overlap" "$combo" "page1 and page2 share $overlap rows"
        rc=1
      fi
    fi
  fi

  # 8. Offset pagination
  if [[ $rc -eq 0 ]]; then
    local off_resp total off_has_next
    off_resp=$(curl -sfS "http://localhost:$PORT/api/v1/orders?offset=0&limit=10" 2>>"$log_file") || rc=1
    total=$(echo "$off_resp" | jq -r '.offset_pagination.total // 0')
    off_has_next=$(echo "$off_resp" | jq -r '.offset_pagination.has_next')
    if [[ "$total" -lt 25 || "$off_has_next" != "true" ]]; then
      fail_step "offset-page1" "$combo" "total=$total has_next=$off_has_next"
      rc=1
    else
      local off_resp2 p1_ids p2_ids overlap
      off_resp2=$(curl -sfS "http://localhost:$PORT/api/v1/orders?offset=10&limit=10" 2>>"$log_file") || rc=1
      p1_ids=$(echo "$off_resp"  | jq -r '.data[].id' | sort)
      p2_ids=$(echo "$off_resp2" | jq -r '.data[].id' | sort)
      overlap=$(comm -12 <(echo "$p1_ids") <(echo "$p2_ids") | wc -l | tr -d ' ')
      if [[ "$overlap" != "0" ]]; then
        fail_step "offset-no-overlap" "$combo" "page1 and page2 share $overlap rows"
        rc=1
      fi
    fi
  fi

  # 9. Cache verification — only meaningful for redis-backed combos. Memory cache
  #    keeps state in-process and isn't observable from outside; "none" has no cache.
  if [[ $rc -eq 0 && "$cache_mode" == "redis" ]]; then
    local keys
    keys=$(docker exec go-scaffolder-redis redis-cli -a admin --no-auth-warning KEYS '*order*' 2>/dev/null)
    if [[ -z "$keys" ]]; then
      fail_step "cache-keys" "$combo" "no redis keys matching *order* — cache layer not exercised?"
      rc=1
    fi
  fi

  # 10. Log verification — request_id field present on at least N lines.
  # `grep -c` exits 1 with output "0" on no-match, which triggers the `|| =0`
  # AND keeps the printed "0", giving us a two-line value that breaks `[[ -lt ]]`.
  # Force a single integer regardless of grep's exit status.
  if [[ $rc -eq 0 ]]; then
    local rid_count
    rid_count=$(grep -c '"request_id"' "$log_file" 2>/dev/null)
    rid_count=${rid_count:-0}
    if [[ "$rid_count" -lt 5 ]]; then
      fail_step "log-request-id" "$combo" "found $rid_count request_id entries, expected at least 5"
      rc=1
    fi
  fi

  # 11. OpenAPI / docs surface — DOCS_ENABLED=true is set in the env block
  # above so huma exposes /openapi.{json,yaml} and /docs. We assert on three
  # things: (a) JSON spec parses and reports OpenAPI 3.1 with the entity
  # routes registered, (b) YAML variant is non-empty, (c) the Stoplight
  # Elements UI shell loads. Each is a separate step so a failure points
  # straight at which layer broke.
  if [[ $rc -eq 0 ]]; then
    local spec openapi_ver paths_ok schemas_ok
    spec=$(curl -sfS "http://localhost:$PORT/openapi.json" 2>>"$log_file") || rc=1
    if [[ $rc -eq 0 ]]; then
      openapi_ver=$(echo "$spec" | jq -r '.openapi // empty')
      paths_ok=$(echo "$spec" | jq '.paths | (has("/api/v1/orders") and has("/api/v1/orders/{id}") and has("/healthz"))')
      # Schema names come from the Go types huma reflects over, so they track
      # httphandler_dto.go.tmpl. POST and PUT share one {Entity}Body — the only
      # difference at the HTTP layer is the path-bound id, already lifted into
      # Update{Entity}Input — so there is no separate Create/Update request
      # schema to assert on.
      #
      # Both pagination envelopes are asserted because the handler exposes
      # cursor and offset from one route, chosen by query param; losing either
      # silently halves the API surface while every CRUD assertion still passes.
      schemas_ok=$(echo "$spec" | jq '.components.schemas | (has("Order") and has("OrderBody") and has("ErrorBody") and has("CursorPagination") and has("OffsetPagination"))')
      if [[ ! "$openapi_ver" =~ ^3\. ]]; then
        fail_step "openapi-json" "$combo" "expected OpenAPI 3.x, got version=$openapi_ver"
        rc=1
      elif [[ "$paths_ok" != "true" ]]; then
        fail_step "openapi-json" "$combo" "missing expected paths: $(echo "$spec" | jq -c '.paths | keys')"
        rc=1
      elif [[ "$schemas_ok" != "true" ]]; then
        fail_step "openapi-json" "$combo" "missing expected schemas: $(echo "$spec" | jq -c '.components.schemas | keys')"
        rc=1
      fi
    fi
  fi

  if [[ $rc -eq 0 ]]; then
    local yaml_status yaml_body
    yaml_status=$(curl -sf -o /tmp/openapi-yaml.$$ -w '%{http_code}' "http://localhost:$PORT/openapi.yaml" 2>>"$log_file") || true
    yaml_body=$(wc -c < /tmp/openapi-yaml.$$ 2>/dev/null || echo 0)
    rm -f /tmp/openapi-yaml.$$
    if [[ "$yaml_status" != "200" || "$yaml_body" -lt 100 ]]; then
      fail_step "openapi-yaml" "$combo" "status=$yaml_status body_bytes=$yaml_body"
      rc=1
    fi
  fi

  if [[ $rc -eq 0 ]]; then
    local docs_html
    docs_html=$(curl -sfS "http://localhost:$PORT/docs" 2>>"$log_file") || rc=1
    if [[ $rc -eq 0 && "$docs_html" != *"elements-api"* ]]; then
      fail_step "docs-ui" "$combo" "Stoplight Elements component not present in /docs response"
      rc=1
    fi
  fi

  # Tear down the production binary before the stub phase reuses the port.
  kill_pid "$pid"
  pid=""

  # 12. Stub mode. Everything above ran the production build, where the stub
  #     package is not even linked in. The compile matrix builds -tags=stub but
  #     never runs it, so until here nothing has executed a line of the stub —
  #     and the factory switch it hangs off has three branches, all unverified.
  #
  #     Worth testing because the failure is silent in the worst direction: a
  #     stub that quietly persists, or a SERVICE_BACKEND=real that quietly
  #     serves canned data, looks exactly like a working service to whoever is
  #     developing a frontend against it.
  if [[ $rc -eq 0 ]]; then
    test_stub_mode "$combo" "$driver" || rc=1
  fi

  if [[ $rc -eq 0 ]]; then
    log "  [pass] $combo"
  fi
  return $rc
}

# test_stub_mode <combo-id> <driver>
# Builds with -tags=stub and exercises both branches of the service factory.
# Returns 0 on pass, 1 on any failure.
test_stub_mode() {
  local combo="$1" driver="$2"
  local out_dir="$OUT_BASE/$combo"
  local log_file="$LOG_BASE/$combo.log"
  local rc=0 pid=""

  if ! (cd "$out_dir" && GOWORK=off go build -tags=stub -o "./bin/svc-stub" "./cmd/smoke-$combo") >>"$log_file" 2>&1; then
    fail_step "stub-build" "$combo" "$(tail -10 "$log_file")"
    return 1
  fi

  local dsn
  case "$driver" in
    postgres)     dsn="$DSN_POSTGRES" ;;
    bun-postgres) dsn="$DSN_BUN_POSTGRES" ;;
    mysql | bun-mysql) dsn="$DSN_MYSQL" ;;
  esac

  # --- SERVICE_BACKEND=stub: canned, stateless, no database required ---------
  #
  # DATABASE_DSN is deliberately unset. The stub's whole purpose is booting a
  # frontend-facing API with no infrastructure, so if it can only start when a
  # database happens to be reachable, that promise is broken and every local
  # `go run -tags=stub` on a laptop without docker fails.
  HTTP_ADDR=":$PORT" SERVICE_NAME="$combo-stub" SERVICE_BACKEND=stub \
  DOCS_ENABLED=true LOG_BODY=true \
  "$out_dir/bin/svc-stub" >>"$log_file" 2>&1 &
  pid=$!

  if ! wait_healthz; then
    fail_step "stub-healthz" "$combo" "stub build did not come up without a database: $(tail -20 "$log_file")"
    kill_pid "$pid"
    return 1
  fi

  local stub_list stub_count first_id
  stub_list=$(curl -sfS "http://localhost:$PORT/api/v1/orders?limit=50" 2>>"$log_file") || rc=1
  if [[ $rc -eq 0 ]]; then
    stub_count=$(echo "$stub_list" | jq -r '.data | length')
    first_id=$(echo "$stub_list" | jq -r '.data[0].id // empty')
    # Deterministic ids are a documented contract: a frontend hardcodes them as
    # fixtures, so they must survive a restart rather than being regenerated.
    if [[ "$stub_count" -lt 1 ]]; then
      fail_step "stub-list" "$combo" "stub returned $stub_count records, expected the canned set"
      rc=1
    elif [[ "$first_id" != order-stub-* ]]; then
      fail_step "stub-canned-ids" "$combo" "first id was '$first_id', expected the deterministic order-stub-N form"
      rc=1
    fi
  fi

  # Writes must not persist. A stub that accumulates state drifts away from the
  # canned fixtures the frontend is coded against, one POST at a time.
  if [[ $rc -eq 0 ]]; then
    curl -sfS -X POST "http://localhost:$PORT/api/v1/orders" \
      -H 'Content-Type: application/json' \
      -d '{"product_code":"STUB-WRITE","quantity":1,"in_stock":true}' >/dev/null 2>>"$log_file" || rc=1
    local after_count
    after_count=$(curl -sfS "http://localhost:$PORT/api/v1/orders?limit=50" 2>>"$log_file" | jq -r '.data | length')
    if [[ "$after_count" != "$stub_count" ]]; then
      fail_step "stub-stateless" "$combo" "record count moved $stub_count -> $after_count; the stub is persisting writes"
      rc=1
    fi
  fi

  kill_pid "$pid"
  pid=""

  # --- SERVICE_BACKEND=real under -tags=stub: the switch must still flip -----
  #
  # This is the branch that matters in production: the binary is built with the
  # tag but must serve real data. If the factory were stuck on the stub, every
  # CRUD assertion above would still pass while the service quietly returned
  # fixtures.
  if [[ $rc -eq 0 ]]; then
    DATABASE_DSN="$dsn" \
    REDIS_ADDR=localhost:6379 REDIS_PASSWORD=admin REDIS_DB=0 \
    HTTP_ADDR=":$PORT" SERVICE_NAME="$combo-stubreal" SERVICE_BACKEND=real \
    DOCS_ENABLED=true LOG_BODY=true \
    "$out_dir/bin/svc-stub" >>"$log_file" 2>&1 &
    pid=$!

    if ! wait_healthz; then
      fail_step "stub-real-healthz" "$combo" "$(tail -20 "$log_file")"
      rc=1
    else
      local real_first
      real_first=$(curl -sfS "http://localhost:$PORT/api/v1/orders?limit=1" 2>>"$log_file" | jq -r '.data[0].id // empty')
      if [[ -z "$real_first" ]]; then
        fail_step "stub-real-list" "$combo" "no rows returned from the real backend"
        rc=1
      elif [[ "$real_first" == order-stub-* ]]; then
        fail_step "stub-real-switch" "$combo" "SERVICE_BACKEND=real still served canned data (id=$real_first) — factory is stuck on the stub"
        rc=1
      fi
    fi
    kill_pid "$pid"
  fi

  return $rc
}

test_consumer() {
  local combo="$1"
  log ""
  log "==> $combo (consumer)"
  log "  [skip] consumer runtime tests not yet implemented (no kafka/rabbitmq in compose)"
  return 0
}

test_publisher() {
  local combo="$1"
  log ""
  log "==> $combo (publisher)"
  log "  [skip] publisher runtime tests not yet implemented (no kafka/rabbitmq in compose)"
  return 0
}

# --- Main ----------------------------------------------------------------------

main() {
  local filter="${1:-}"

  if [[ "$filter" == "--list" ]]; then
    log "Combos that would run:"
    for entry in "${COMBOS[@]}"; do
      log "  ${entry%%|*}"
    done
    exit 0
  fi

  for cmd in docker jq curl go; do require_cmd "$cmd"; done

  # Verify the test port is free before any combo runs; a stolen port causes
  # wait_healthz to silently pass against a foreign service.
  if lsof -i ":$PORT" >/dev/null 2>&1; then
    log "ERROR: port $PORT is already in use (run: lsof -i :$PORT). Change PORT= or free the port first."
    exit 2
  fi
  if ! docker compose version >/dev/null 2>&1; then
    log "ERROR: 'docker compose' subcommand not available"
    exit 2
  fi

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    log "ERROR: docker-compose.yml not found at $COMPOSE_FILE"
    exit 2
  fi

  log "Bringing up postgres + mysql + redis (if not already up)..."
  if ! docker compose -f "$COMPOSE_FILE" up -d --wait postgres mysql redis 2>&1 | tail -5; then
    log "ERROR: docker compose up failed"
    exit 2
  fi

  mkdir -p "$LOG_BASE" "$OUT_BASE"

  local pass=0 fail=0 skip=0
  for entry in "${COMBOS[@]}"; do
    local combo="${entry%%|*}"
    local rest="${entry#*|}"
    local driver="${rest%%|*}"
    local cache_mode="${rest##*|}"

    if [[ -n "$filter" ]] && [[ "$combo" != *"$filter"* ]]; then
      ((skip++))
      continue
    fi

    if test_api "$combo" "$driver" "$cache_mode"; then
      ((pass++))
    else
      ((fail++))
    fi
  done

  log ""
  hr
  log "$pass passed, $fail failed, $skip filtered out (total ${#COMBOS[@]})"
  if [[ $fail -gt 0 ]]; then
    log "Inspect logs under $LOG_BASE/"
    exit 1
  fi
  exit 0
}

main "$@"
