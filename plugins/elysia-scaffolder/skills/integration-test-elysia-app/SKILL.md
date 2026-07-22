---
name: integration-test-elysia-app
description: Run an end-to-end integration test for a elysia-scaffolder-generated service against a real postgres + redis docker stack. Renders the api+postgres+redis combo from the live templates, seeds the DB, boots the Bun service in real mode, and asserts CRUD + cursor pagination (no-overlap) + redis cache-key presence + request_id-in-logs + the 404 error envelope. **Use this whenever the user says "test the scaffolded Elysia app", "run the integration test", "verify the generated service works against real postgres/redis", "smoke-test the runtime", or any phrasing that implies running real HTTP requests against a scaffolded Elysia service and live database/redis.** Compile-only type-checking (the smoke runner) is a different thing — this skill actually boots the binary and exercises real endpoints.
allowed-tools: [bash, read]
model: inherit
---

# Skill: integration-test-elysia-app

End-to-end runtime verification for services scaffolded by `elysia-scaffolder`.
The driver lives at `${CLAUDE_SKILL_DIR}/scripts/run.sh` — do a friendly pre-flight,
invoke it, and translate the output.

It renders the `api+postgres+redis` combo from the **live templates** (so it tests the
actual `.tmpl` files, not a fixture), brings up docker, seeds 25 rows, boots the service
in `SERVICE_BACKEND=real` mode, and asserts the full sequence.

## Step 1 — Pre-flight

```bash
for cmd in bun docker jq curl; do command -v "$cmd" >/dev/null || { echo "MISSING: $cmd"; exit 2; }; done
echo "preflight OK"
```

Surface any missing tool to the user (one-command fixes). Do not install on their behalf.
`@labspangaea/ts-lib` is a public npm package — `bun install` pulls it from the public
registry, so there is nothing to check out or point at locally.

## Step 2 — Invoke

```bash
${CLAUDE_SKILL_DIR}/scripts/run.sh
```

The script handles everything: render → `docker compose up -d --wait` → `bun install` →
`tsc --noEmit` → seed → boot on `:8099` → assertions → SIGTERM. The rendered package.json
pins the public `@labspangaea/ts-lib` (`^0.1.0`), so `bun install` fetches it from the
public registry — no local checkout or repointing.

## Step 3 — Report

The script prints `[pass]`/`[FAIL]` per assertion and a final `N passed, N failed`. The
assertions: `create+get round-trip`, `created_at valid ISO`, `cursor page1 = 10`,
`page1/page2 no overlap`, `redis cache key present`, `delete -> 204`, `deleted -> 404`,
`404 envelope error_code`, `request_id in >=5 log lines`. On failure, the booted service's
full stdout/stderr is at `${CLAUDE_SKILL_DIR}/logs/api-postgres-redis.log` — read the last
~30 lines for the user (DSN parse, drizzle, redis dial, etc.).

## Step 4 — Optional teardown

After reporting, ask whether to tear down the docker stack:

```bash
docker compose -f "${CLAUDE_SKILL_DIR}/out/api-postgres-redis/docker-compose.yml" down -v
```

Default: leave it up so the user can iterate. Only tear down on a yes.

## What this skill does NOT do
- **Consumer/publisher runtime** — needs kafka/rabbitmq, not in the compose stack (deferred).
- **Couchbase / memory cache combos** — redis is the runtime-covered cache backend.
- **Stub-mode assertions** — this skill is real-service only (`SERVICE_BACKEND=real`).
- **Offset pagination** — the controller template ships cursor pagination; offset is a follow-up.
- **OTel trace export** — verifies `request_id` in logs as evidence of context propagation.
- **Auth / load testing** — functional verification only.
- **Type-check the templates** — that's the smoke runner (`tools/smoke`), a separate concern.
