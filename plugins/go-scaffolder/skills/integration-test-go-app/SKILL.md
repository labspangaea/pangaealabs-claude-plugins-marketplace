---
name: integration-test-go-app
description: Run end-to-end integration tests for a go-scaffolder-generated Go service against the bundled docker-compose stack (postgres + mysql + redis). Use this skill whenever the user says "test the scaffolded Go app", "run integration tests on the API combos", "verify CRUD/pagination/cache works for nethttp/gin/chi/mux/echo", "smoke-test the runtime", "test the generated handlers against real services", or any phrasing that implies running real HTTP requests against scaffolded services and live database/redis containers. Tests both cursor and offset pagination, verifies cache keys appear in redis, asserts request_id appears in the structured logs, and validates the huma OpenAPI 3.1 spec + Stoplight Elements UI at /openapi.{json,yaml} and /docs. Compile-only smoke testing (the `tools/smoke -all` runner) is a different thing — this skill actually starts each binary and exercises real endpoints.
allowed-tools: [bash, read]
model: sonnet
---

# Skill: integration-test-go-app

End-to-end runtime verification for services scaffolded by `go-scaffolder`. The heavy lifting lives in the bundled bash driver at `${CLAUDE_SKILL_DIR}/scripts/run.sh` — your job here is to do a friendly pre-flight, invoke the script, and translate its output for the user.

The compile-only smoke runner at `tools/smoke/` proves the templates compile. This skill is the next layer up: it actually starts each generated binary, hits real HTTP endpoints, and asserts on the responses + cache state + log content. If smoke says 16/16 pass but this skill fails, the bug is in the runtime wiring (config, env vars, service code path), not the templates.

## Step 1: Pre-flight checks

Run a single bash block to fail fast with a clear message if any prerequisite is missing. The script does its own checks too, but doing them here means the user gets actionable errors before docker even spins up:

```bash
COMPOSE="$HOME/projects/claude-plugins/plugins/go-scaffolder/docker-compose.yml"

for cmd in docker jq curl go; do
  command -v "$cmd" >/dev/null || { echo "MISSING: $cmd not on PATH"; exit 2; }
done

[ -f "$COMPOSE" ] || { echo "MISSING: docker-compose.yml at $COMPOSE"; exit 2; }

echo "preflight OK"
```

If any check fails, surface the exact line to the user — most of these are one-command fixes (install jq, etc.). Do not try to install on the user's behalf; that's their decision. `go-lib` itself needs no preflight — it's a public module the driver's `go mod tidy` fetches from the proxy.

## Step 2: Confirm scope (default 5 combos vs. filter)

If the user passed a framework name as an argument (e.g., `nethttp`, `echo`), pass it through as a filter so only matching combos run. Otherwise the default set runs:

| Combo | Framework | DB | Cache |
|---|---|---|---|
| `api-nethttp-postgres-redis` | nethttp | postgres | redis |
| `api-gin-postgres-memory` | gin | postgres | in-process memory |
| `api-mux-postgres-none` | mux | postgres | none |
| `api-echo-postgres-redis` | echo | postgres | redis |
| `api-nethttp-mysql-none` | nethttp | mysql | none |

**Chi is currently uncovered** at runtime — the only existing chi combo is `api-chi-mysql-couchbase`, and couchbase isn't in the docker-compose stack. To add chi coverage, append `api-chi-postgres-redis` to `tools/smoke/combos.go` and add the same line to `${CLAUDE_SKILL_DIR}/scripts/run.sh`'s `COMBOS` array. That's a separate task; flag the gap to the user only if they ask why chi is missing.

Consumer and publisher combos (kafka/rabbitmq/redis-broker types) need broker services not in the compose file. The script returns `[skip]` for them with the reason printed. This is intentional — adding kafka + rabbitmq is its own follow-on piece of work.

## Step 3: Invoke the bundled driver

```bash
${CLAUDE_SKILL_DIR}/scripts/run.sh [optional-filter]
```

The script handles everything from here: `docker compose up -d --wait postgres mysql redis`, then for each combo it renders via `tools/smoke -render`, runs `go mod tidy`, drops + recreates the `orders` table (so each run starts clean — important because every combo seeds 26 entities for pagination), starts the binary on `:8080` with `DOCS_ENABLED=true` and `LOG_BODY=true`, polls `/healthz`, runs the assertion sequence (CRUD → cursor → offset → cache → logs → OpenAPI/docs), and SIGTERMs the binary before moving on.

We drop the orders table per combo because pagination assertions check exact row counts (`offset_pagination.total >= 25` after seeding 25). Leftover rows from a prior combo would inflate the count and make false positives look like real passes — the cleanup keeps the test signal honest.

The combos run **sequentially on port 8080** (one starts, dies, next starts). That's slow but trivial — and trying to parallelize means dealing with port allocation, port-conflict bugs in the test harness, and noisier failure attribution. Sequential is the right tradeoff.

## Step 4: Report results

Each combo emits exactly one of these lines to stdout:

- `  [pass] <combo-id>` — every assertion passed (CRUD + cursor + offset + cache + logs + OpenAPI/docs)
- `  [FAIL] <step> — <combo-id>` followed by indented diagnostic lines — one of the assertions failed; the step name tells you which one (`render`, `go mod tidy`, `wait_healthz`, `create`, `find`, `update`, `delete`, `seed-N`, `cursor-page1`, `cursor-no-overlap`, `offset-page1`, `offset-no-overlap`, `cache-keys`, `log-request-id`, `openapi-json`, `openapi-yaml`, `docs-ui`)
- `  [skip] <combo-id>` — consumer/publisher placeholder

Final line: `<N> passed, <N> failed, <N> filtered out (total <N>)`.

When something fails, the binary's full stdout/stderr lives at `${CLAUDE_SKILL_DIR}/logs/<combo>.log`. Read the last ~30 lines for the user; that's almost always where the actual error is (DSN parsing, GORM auto-migrate, redis dial, etc.). Don't dump the whole log — it's noisy.

Re-running the skill is idempotent. The drop-table step ensures every run starts with a clean schema; rendered output under `${CLAUDE_SKILL_DIR}/out/` is wiped per combo before re-rendering.

## Step 5: Optional teardown

After reporting results, ask the user whether to tear down the docker-compose services:

```bash
docker compose -f "$HOME/projects/claude-plugins/plugins/go-scaffolder/docker-compose.yml" down -v
```

Default behavior: **leave services running** so the user can iterate quickly (re-run the skill, poke at the running redis manually, etc.). Only tear down when the user says yes — they may want the stack up for other work.

## Stub mode is out of scope

Scaffolded services ship with a service-level canned-response stub gated by `//go:build stub` (see `create-go-app/SKILL.md` — "Stub mode — FE/BE parallel development"). This skill always tests **the real service path**:

- The integration binary is built **without** `-tags=stub`, so the stub package is not linked in and `factory_default.go` always returns the production service.
- `run.sh` sets `SERVICE_BACKEND=real` explicitly as a belt-and-braces guard against a future flip to `-tags=stub` silently routing CRUD assertions through the stub.
- The scaffolder's `.env` default of `SERVICE_BACKEND=stub` is the right default for `go run -tags=stub ./cmd/...` (the FE-integration scenario) — it does not affect this skill.

Stub-mode runtime verification (boot without docker, assert canned responses on /orders, OpenAPI still served at /docs) is a separate concern. If/when it's needed, run it as its own combo class — not bolted onto these CRUD assertions, since the stub is intentionally stateless and would fail every Create→Find round-trip check.

## What this skill does NOT do

- **Test consumer/publisher runtime behavior** — needs kafka/rabbitmq, deferred until those services land in docker-compose.
- **Test couchbase cache combos** — same reason (no couchbase service).
- **Test stub-mode behavior** — see "Stub mode is out of scope" above; this skill is real-service only.
- **Verify OTel trace export** — would need a trace collector; the test does verify `request_id` appears in logs, which is sufficient evidence that the request-context propagation works end-to-end.
- **Authentication / RBAC tests** — generated services don't ship with auth.
- **Concurrency or load testing** — this is functional verification, not throughput.
- **Compile-test the templates** — that's `tools/smoke -all`, separate concern.
