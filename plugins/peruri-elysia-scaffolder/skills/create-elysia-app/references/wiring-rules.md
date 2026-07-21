# Wiring Rules — composition root + layer contracts

Non-negotiable MUST / MUST NOT rules the generated code follows. The templates
already conform; consult this when hand-editing `src/index.ts` or the `src/*`
layers.

## Foundational (all types)

| Rule | Do | Don't |
|---|---|---|
| Logger init | `createLogger({ serviceName, version, instanceId })` once at the composition root | construct loggers per-request by hand |
| Logger retrieval | `logger.fromContext()` inside any method below the handler | thread a `Logger` param through every function, or read a global |
| Request context | the `serverPlugin` seeds AsyncLocalStorage per request (request_id-bound child logger) | mutate a shared `store` for per-request data (racy) |
| No hardcoded timeouts | all durations come from `cfg.*` (env-backed) | literal `5000` / `30_000` in `index.ts` |
| Graceful shutdown | `process.on('SIGTERM'…)` → `app.stop()` → `closeDb` → `redis.disconnect()`, raced against `cfg.httpShutdownTimeoutMs` | `process.exit()` without draining |

## HTTP (api)

| Rule | Do | Don't |
|---|---|---|
| Middleware | `.use(serverPlugin({ logger, serviceName }))` first, then health, then the entity controller | re-implement request-id / logging / recover by hand |
| Error dispatch | `throw new ApiError(ErrXxx)` from the controller/service | build `{status:false,…}` JSON in a handler |
| Validation | TypeBox `body:` schema on the route — drives runtime validation AND OpenAPI | a manual validation pass or a second validator lib |
| Success | `data(entity)` / `list(rows.map(toResponse), withCursor({…}))` | return bare objects (loses the envelope) |
| Cursor | `cursorParamsFromQuery(sp, 20, desc('created_at'), asc('id'))` | parse cursor/limit by hand |
| Wire mapping | `bodyToInput` (snake→camel) + `toResponse` (camel→snake, Date→ISO) | serialize the camelCase domain directly (wire drift vs the Go service) |

## Error codes (api)

| Rule | Do | Don't |
|---|---|---|
| Definition | `src/apperr/{entity}.ts`, `appendCodeErrMap(...)` at module load, base offset (scan existing + 1000) | register codes inside handlers |
| Side-effect import | `import './apperr/{entity}.ts'` in `index.ts` so codes register | rely on the repository import alone (tree-shaking risk) |
| No domain sentinels | named errors live in `apperr/` as `CodeErrEnum` | `export const ErrNotFound = new Error(...)` in `domain/` |
| Repo mapping | repo maps `repo.ErrNotFound` → `new ApiError(ErrXxxNotFound)` | let `repo.ErrNotFound` leak past the adapter |

## Repository (api, consumer)

| Rule | Do | Don't |
|---|---|---|
| Generic base | wrap `makeRepository(db, meta)` / `makeCachedRepository(...)` over a snake_case `{Entity}Row` + `ModelMeta` | hand-write SQL in the service |
| Date coercion | `new Date(Number(r.created_at))` — Postgres bigint arrives as a string | `new Date(r.created_at)` (→ Invalid Date) |
| Update columns | pass an explicit column list to `update` (never `id`/`created_at`) | update all columns (clobbers immutables) |
| Cache prefix | the prefix is the 3rd arg to `makeCachedRepository`; do NOT also prefix the backend | double-prefix keys |

## Service (api)

| Rule | Do | Don't |
|---|---|---|
| DIP | the service depends on `port.{Entity}Repository` only | import the concrete Drizzle adapter |
| Service port | the controller depends on `port.{Entity}Service`; both real + stub implement it | the controller importing `service/{entity}.ts` directly |
| Factory | `new{Entity}Service(cfg, repo)` selects real vs stub | `new {Entity}ServiceImpl(repo)` in `index.ts` |
| Stub build tag | the stub branch is gated by `SERVICE_STUB` (tree-shaken from prod `bun build`) | ship the stub linked into prod |
| Stub statelessness | stub create/update/delete are no-ops returning canned data | a stub that pretends to persist (append to a slice) |

## Cross-cutting

| Rule | Do | Don't |
|---|---|---|
| Outbound HTTP | use `@peruri/ts-lib/client` (auto-propagates the request logger) | a bare `fetch` with no trace/log context |
| Pub/Sub handler (consumer) | do NOT bind the handler to a shutdown AbortSignal (the `context.WithoutCancel` analogue) | abort in-flight handlers on broker disconnect |
