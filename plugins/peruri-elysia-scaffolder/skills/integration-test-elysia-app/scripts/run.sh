#!/usr/bin/env bash
# Integration-test driver for peruri-elysia-scaffolder.
#
# Renders the api+postgres+redis combo from the live templates, brings up a
# postgres+redis docker stack, seeds 25 rows, boots the generated service in
# real mode, and runs a CRUD -> cursor-pagination -> cache-key -> request_id-log
# assertion sequence against real HTTP. Proves the *templates* produce a working
# runnable service (the next layer up from the smoke type-check).
#
# Env:
#   PERURI_TS_LIB   path to the @peruri/ts-lib checkout (default ~/projects/peruri-ts-lib)
#   PORT            service port (default 8099)
set -uo pipefail

PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REF="$PLUGIN/skills/create-elysia-app/references"
RENDERER="$PLUGIN/tools/render-file/index.ts"
LIB="${PERURI_TS_LIB:-$HOME/projects/peruri-ts-lib}"
PORT="${PORT:-8099}"
OUT="$PLUGIN/skills/integration-test-elysia-app/out/api-postgres-redis"
LOGDIR="$PLUGIN/skills/integration-test-elysia-app/logs"
mkdir -p "$LOGDIR"

# ---- preflight -------------------------------------------------------------
for cmd in bun docker jq curl; do
  command -v "$cmd" >/dev/null || { echo "MISSING: $cmd not on PATH"; exit 2; }
done
[ -d "$LIB" ] || { echo "MISSING: @peruri/ts-lib at $LIB (set PERURI_TS_LIB)"; exit 2; }
echo "preflight OK (lib=$LIB)"

# ---- render the combo ------------------------------------------------------
rm -rf "$OUT"; mkdir -p "$OUT"
PARAMS='{"Name":"order-service","Module":"@peruri/order-service","Entity":"Order","EntityLower":"order","ApperrBase":1000,"Type":"api","Broker":"kafka","Database":"drizzle-postgres","Cache":"redis","Fields":[{"Name":"customerId","GoType":"string","JSONName":"customer_id","DBColumn":"customer_id","Validate":"required,max=64"},{"Name":"total","GoType":"number","JSONName":"total","DBColumn":"total","Validate":"required"},{"Name":"note","GoType":"string | null","JSONName":"note","DBColumn":"note","Validate":""}]}'
r(){ bun "$RENDERER" -template "$REF/$1" -params "$PARAMS" -output "$OUT/$2" || { echo "render failed: $1"; exit 2; }; }
r config.ts.tmpl config/config.ts
r domain.ts.tmpl src/domain/order.ts
r port.ts.tmpl src/port/order.ts
r port_service.ts.tmpl src/port/order-service.ts
r service.ts.tmpl src/service/order.ts
r service_stub.ts.tmpl src/service/stub/order.ts
r service_factory.ts.tmpl src/service/factory.ts
r apperr.ts.tmpl src/apperr/order.ts
r schema.ts.tmpl src/db/schema/order.ts
r repository.ts.tmpl src/adapter/outbound/repository/order.ts
r controller.ts.tmpl src/adapter/inbound/http/order.ts
r dto.ts.tmpl src/adapter/inbound/http/order.dto.ts
r health.ts.tmpl src/adapter/inbound/http/health.ts
r index_api.ts.tmpl src/index.ts
r seed.ts.tmpl src/cmd/seed.ts
r drizzle.config.ts.tmpl drizzle.config.ts
r package.json.tmpl package.json
r tsconfig.json.tmpl tsconfig.json
r docker-compose.yml.tmpl docker-compose.yml
r env.tmpl .env
echo "rendered $(find "$OUT" -name '*.ts' | wc -l | tr -d ' ') .ts files"

# Point @peruri/ts-lib at the absolute checkout (the template default file:../ is
# relative to a generated sibling; the test OUT dir is elsewhere).
node -e "const f='$OUT/package.json';const j=require(f);j.dependencies['@peruri/ts-lib']='file:'+'$LIB';require('fs').writeFileSync(f,JSON.stringify(j,null,2))" 2>/dev/null \
  || sed -i '' "s|file:../peruri-ts-lib|file:$LIB|" "$OUT/package.json"

# ---- stack + install + typecheck ------------------------------------------
( cd "$OUT" && docker compose up -d --wait ) || { echo "docker compose up failed"; exit 2; }
( cd "$OUT" && bun install >/dev/null 2>&1 ) || { echo "bun install failed"; exit 2; }
( cd "$OUT" && ./node_modules/.bin/tsc --noEmit ) || { echo "[FAIL] tsc"; exit 1; }
echo "tsc clean"
( cd "$OUT" && SERVICE_BACKEND=real bun run src/cmd/seed.ts ) || { echo "[FAIL] seed"; exit 1; }

# ---- boot + assert ---------------------------------------------------------
LOG="$LOGDIR/api-postgres-redis.log"
# Kill any leftover service from a prior aborted run (would hold $PORT and serve
# stale/wedged responses to our curls).
pkill -f "$OUT/src/index.ts" 2>/dev/null || true
cleanup_svc() { [ -n "${SV:-}" ] && kill "$SV" 2>/dev/null; pkill -f "$OUT/src/index.ts" 2>/dev/null; }
trap cleanup_svc EXIT
# `exec env … bun` so $SV is the bun PID itself (not a wrapping subshell), so the
# kill below actually stops the server instead of orphaning it.
( cd "$OUT" && exec env SERVICE_BACKEND=real PORT=$PORT DB_LOG_LEVEL=warn REDIS_PASSWORD=admin bun run src/index.ts ) >"$LOG" 2>&1 &
SV=$!
curl -sf --retry 40 --retry-delay 1 --retry-connrefused "http://localhost:$PORT/healthz" >/dev/null 2>&1
B="http://localhost:$PORT/api/v1/orders"
pass=0; fail=0
chk(){ if [ "$1" = "$2" ]; then echo "  [pass] $3"; pass=$((pass+1)); else echo "  [FAIL] $3 (got '$1' want '$2')"; fail=$((fail+1)); fi; }

ID=$(curl -s -X POST "$B" -H 'content-type: application/json' -d '{"customer_id":"it","total":10.5,"note":"x"}' | jq -r '.data.id')
chk "$(curl -s "$B/$ID" | jq -r '.data.customer_id')" "it" "create+get round-trip"
chk "$(curl -s "$B/$ID" | jq -r '.data.created_at' | grep -c T)" "1" "created_at valid ISO"
P1=$(curl -s "$B?limit=10")
chk "$(echo "$P1" | jq '.data|length')" "10" "cursor page1 = 10"
NEXT=$(echo "$P1" | jq -r '.cursor_pagination.next_cursor')
chk "$(comm -12 <(echo "$P1"|jq -r '.data[].id'|sort) <(curl -s "$B?limit=10&cursor=$NEXT"|jq -r '.data[].id'|sort) | wc -l | tr -d ' ')" "0" "page1/page2 no overlap"
curl -s "$B/$ID" >/dev/null
CACHEKEYS=$( cd "$OUT" && docker compose exec -T redis redis-cli -a admin --no-auth-warning KEYS 'order:*' 2>/dev/null | grep -c order )
chk "$([ "$CACHEKEYS" -ge 1 ] && echo yes || echo no)" "yes" "redis cache key present"
chk "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$B/$ID")" "204" "delete -> 204"
NF=$(curl -s -w '\n%{http_code}' "$B/$ID")
chk "$(echo "$NF"|tail -1)" "404" "deleted -> 404"
chk "$(echo "$NF"|head -1|jq -r '.error_code')" "ERR404100" "404 envelope error_code"
chk "$([ "$(grep -c '\"request_id\"' "$LOG")" -ge 5 ] && echo yes || echo no)" "yes" "request_id in >=5 log lines"

# OpenAPI (DOCS_ENABLED=true from the rendered .env)
chk "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/docs")" "200" "openapi /docs serves"
chk "$(curl -s "http://localhost:$PORT/docs/json" | grep -c '"openapi"')" "1" "openapi spec at /docs/json"
# malformed cursor -> 400 (client error), not 500
chk "$(curl -s -o /dev/null -w '%{http_code}' "$B?cursor=not-a-real-cursor")" "400" "invalid cursor -> 400"
# unknown route -> 404, not 500
chk "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/no-such-route")" "404" "unknown route -> 404"

kill $SV 2>/dev/null; wait $SV 2>/dev/null
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ] || { echo "see $LOG"; exit 1; }
echo "ALL PASS"
