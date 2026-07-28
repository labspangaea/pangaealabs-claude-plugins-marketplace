# Dev environment bootstrap

After `bunx tsc --noEmit` passes, bring the stack up and exercise the endpoints.

## 1. Start postgres + redis

```bash
docker compose up -d --wait
```

## 2. Seed the database (25 deterministic rows)

```bash
# Bun auto-loads .env (DATABASE_DSN); the seed creates the table + inserts 25 rows.
SERVICE_BACKEND=real bun run src/cmd/seed.ts
```

## 3. Run the service

**Stub mode (FE integration — no DB/Redis needed):**
```bash
SERVICE_BACKEND=stub bun run src/index.ts     # canned, shape-correct responses
```

**Real mode (full stack):**
```bash
SERVICE_BACKEND=real bun run src/index.ts
```

## 4. Smoke the endpoints

```bash
curl http://localhost:8080/healthz                       # {"status":true,"data":"ok"}
curl http://localhost:8080/version
curl 'http://localhost:8080/api/v1/{entityLower}s?limit=10'
curl -X POST http://localhost:8080/api/v1/{entityLower}s \
  -H 'content-type: application/json' -d '{ … snake_case body … }'
```

## Host vs container DSN

- `.env` uses `localhost` host addresses so `bun run` works from the host (and
  the seed runs against the mapped DB port).
- In a containerized deploy, override `DATABASE_DSN` / `REDIS_ADDR` to the docker
  network hostnames (`postgres`, `redis`) via the container's environment — the
  app reads them from env, no code change.

## Iterate without rebuilding

`bun run src/index.ts` hot-reloads on file changes (`bun --watch run src/index.ts`
for explicit watch). No build step needed for dev; `bun build` is only for the
production/stub binaries (see `/create-elysia-app` "Stub mode").

## Production / stub builds

```bash
bun build ./src/index.ts --target bun --outdir dist                          # prod (stub tree-shaken out)
bun build ./src/index.ts --target bun --define SERVICE_STUB=true --outdir dist-stub  # stub-enabled
```
