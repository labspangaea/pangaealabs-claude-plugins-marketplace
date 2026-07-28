# Wiring Rules — `create-go-app` composition root

This reference enumerates every MUST / MUST NOT rule that the generated `cmd/{name}/main.go` (and its surrounding `internal/*` files) must satisfy when this skill scaffolds an `api`, `consumer`, or `publisher`. Read this file before emitting the composition root — these rules encode the team's hexagonal conventions, error-handling contract, huma validation policy, and stub-mode build constraints. None of these rules are negotiable.

The wider entry-point skill (`SKILL.md`) keeps only a short "highlights" preview of the most-violated rules. The full row-by-row table lives here so the entry point stays under the budget. Templates in `references/*.tmpl` already conform to these rules — if hand-tweaking generated code, validate every edit against the table below.

## Table of contents

- [Foundational wiring](#foundational-wiring) — logger, telemetry, DB, cache
- [HTTP layer](#http-layer) — middleware, response envelopes, error dispatch, validation
- [Error codes](#error-codes) — `apperr` package conventions
- [Repository layer](#repository-layer) — BaseRepo, model contract, cursor wiring
- [Service layer](#service-layer) — port, factory, stub build-tag rules
- [Cross-cutting](#cross-cutting) — config posture, outbound HTTP, pub/sub context

## Foundational wiring

**MUST NOT guess — copy exact patterns from `references/*.tmpl`.**

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| Logger init | MUST | `logger.New(...)` → `logger.WithLogger(ctx, log)` at composition root | all |
| Logger retrieval | MUST | `l := logger.FromContext(ctx)` inside methods — **never inject as struct field** | all |
| Telemetry | MUST | copy exact `telemetry.Setup(...)` bootstrap from main template — the env-driven option assembly (`OTelProtocol` / `OTelInsecure` / `OTelHeaders`) plus the optional `OTelLogBridgeEnabled` rebuild branch; `defer otelShutdown(ctx)`; non-fatal | all |
| DB postgres | MUST | `db.Open(postgres.Open(cfg.DatabaseDSN), ...)` + `defer db.Close(gormDB)` | api, consumer |
| DB mysql | MUST | same as postgres — swap to `gorm.io/driver/mysql` + `mysql.Open` | api, consumer |
| DB none | MUST | omit DB block and `repository/` folder; remove repo arg from `service.New` | all |
| Cache none | MUST | call `repository.New(gormDB)`; omit cache backend init, omit cache fields from config, omit `NewCached` and `cache` import from `repository.go` | api, consumer |
| Cache != none | MUST | construct backend client → `cache.Cache[*{{.Entity}}Model]` → call `repository.NewCached(gormDB, c, repo.WithTTL(cfg.CacheTTL), repo.WithJitter(cfg.CacheJitterFactor), repo.WithTwoPhaseList())` | api, consumer |
| Cache key prefix | MUST | the `repository.NewCached` constructor passes `"{{.EntityLower}}"` as the prefix; do **not** also set `WithKeyPrefix` on the cache backend (would double-prefix) | api, consumer |
| Cache backend type param | MUST | construct as `<backend>.New[*{{.Entity}}Model](...)` — the model pointer, not the domain type — `CachedRepo` caches the SQL row | api, consumer |
| Two-phase list | SHOULD | enable via `repo.WithTwoPhaseList()` only after profiling confirms cache hit rate > ~70%; default scaffold includes it but document the caveat in main.go as a comment | api, consumer |
| Config Kafka fields | MUST NOT | include `KafkaBrokers`, `Topic`, `ConsumerGroup` for `api` type | api |
| Config Kafka fields | MUST | include `KafkaBrokers`, `Topic`, `ConsumerGroup` for `consumer`/`publisher` | consumer, publisher |
| No hardcoded timeouts | MUST NOT | hardcode `time.Second` / `time.Millisecond` literals in `main.go` — all timeouts (`ReadTimeout`, `WriteTimeout`, `IdleTimeout`, `ShutdownTimeout`, `DBSlowThreshold`) MUST come from `cfg.*` fields backed by `envDurationOr` in `config.go` | all |

## HTTP layer

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| HTTP middleware order | MUST | `Recover` → `RequestID` → `otelhttp.NewMiddleware` → `Logging` | api |
| HTTP success response | MUST | `return humares.Data(entity), nil` | api |
| HTTP cursor list response | MUST | `return humares.List(entities, humares.WithCursor[[]*T](&humares.CursorPagination{...})), nil` | api |
| HTTP offset list response | MUST | `return humares.List(entities, humares.WithOffset[[]*T](&humares.OffsetPagination{...})), nil` | api |
| HTTP error dispatch | MUST | `return nil, err` from huma handler — the `huma.NewError` override in main routes through `humares.NewError`; `apierr.CodeErr`/`CodeErrEnum` set HTTP status via `huma.StatusError` | api |
| Request validation | MUST | use huma's native JSON Schema validation only — no go-playground/validator. Fields without `,omitempty` in the json tag are required; `maxLength:"N"` adds the schema constraint. Do NOT add `SkipValidateBody: true` or any `Resolve()` method. No `validate.go` file. | api |
| Cursor params | MUST | `repo.NewCursorParams(input.Cursor, input.Limit, repo.Descending("created_at"), repo.Asc("id"))` in handler — uses huma input fields, not the request directly | api |
| List filter wiring | MUST | request struct implements `ToFilters() []repo.Filter` (Filterable pattern) — not inline in handler | api |

## Error codes

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| API error codes | MUST | define in `internal/apperr/{entity}.go`; register via `apierr.AppendCodeErrMap` in `init()`; use `{{.ApperrBase}}` offset (skill computes: scan existing files, max+1000, default 1000) | api |
| ErrNotFound mapping | MUST | repo maps `repo.ErrNotFound` → `apperr.ErrXxxNotFound` directly; service just wraps with `fmt.Errorf("...: %w", err)` — `apperr.ErrXxxNotFound` is a `CodeErrEnum` which implements `huma.StatusError`, so huma sets the registered HTTP status; no `domain.ErrNotFound` sentinel needed | api |
| No domain error sentinels | MUST NOT | define `var ErrNotFound = errors.New("not found")` in `domain/` — all named errors belong in `internal/apperr/{{.EntityLower}}.go` as `CodeErrEnum` constants registered in `init()` | api |
| Inline error literals | MUST NOT | use inline `fmt.Errorf(...)` passed to `apierr.CodeErrBadRequest.WithDetail` in handlers — define named errors in `internal/apperr/{{.EntityLower}}.go` and `return nil, apperr.ErrXxx` from the huma handler | api |

## Repository layer

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| BaseRepo embedding | MUST | `*repo.BaseRepo[model, ID]` embedded in repository struct; `New` delegates to `repo.New[...]` | api, consumer |
| Model interface | MUST | GORM model must implement `TableName()`, `PrimaryKey()`, `GetPK()`, `CursorValues()` | api, consumer |
| CursorValues | MUST | return values for every column that may appear in `OrderBy`; `filterCursorValues` trims to active sort keys | api, consumer |

## Service layer

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| Service port | MUST | `port.{{.Entity}}Service` defined in `internal/port/{{.EntityLower}}_service.go`; handler depends on this port (structurally or by import) — never on concrete `*service.{{.Entity}}` | api |
| Service factory | MUST | `service.New{{.Entity}}Service(cfg, repo)` from main.go — never call concrete `service.New(repo)` from main.go. Real factory lives in `internal/service/factory_default.go` (//go:build !stub); stub-switching factory in `factory_stub.go` (//go:build stub) | api |
| Stub build tag | MUST | every file in `internal/service/stub/` starts with `//go:build stub` + `// +build stub` so the package is excluded from production binaries | api |
| Service backend selector | MUST | config has `ServiceBackend string` field loaded from `SERVICE_BACKEND` env (default `"stub"`). Only consulted under `-tags=stub`; default builds ignore it. Invalid values panic loudly at startup, never silently fall through | api |
| Real service ↔ port assertion | MUST | `var _ port.{{.Entity}}Service = (*{{.Entity}})(nil)` compile-time check in `internal/service/{{.EntityLower}}.go` | api |
| Stub service ↔ port assertion | MUST | `var _ port.{{.Entity}}Service = (*{{.Entity}})(nil)` compile-time check in `internal/service/stub/{{.EntityLower}}.go` | api |
| Stub statelessness | MUST | `stub.<Entity>` Create/Update/Delete are no-ops that return nil — must NOT pretend to persist (don't append to a shared slice). Subsequent List/Find return the same canned data. Stateful CRUD is the real service's job. | api |
| Stub canned IDs | MUST | seed data uses deterministic IDs (`"<entityLower>-stub-<i>"`) so FE can hardcode test fixtures across restarts | api |

## Cross-cutting

| Concern | Severity | Rule | Applies to |
|---------|----------|------|-----------|
| Pub/Sub handler ctx | MUST | `context.WithoutCancel(ctx)` inside subscriber handlers | consumer |
| Outbound HTTP | SHOULD | `client.NewClient(log)` — auto-propagates OTel trace context | all |
