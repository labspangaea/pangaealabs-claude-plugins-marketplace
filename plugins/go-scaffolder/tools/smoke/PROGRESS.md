# Smoke Hook Progress

The smoke hook at `.claude/hooks/smoke/` validates skill template changes by
rendering combos and running `go build`. Coverage is incremental — only
templates listed in `b1Ready` (in `combos.go`) are checked. Combos depending
on any template not in `b1Ready` are skipped with a clear log message.

## To continue this work in a future session

1. Read this file.
2. Pick the next un-converted template (top of "Pending" list below).
3. Convert any `// SCAFFOLD: ...` prose comments and per-framework hardcoded
   imports to explicit Go `text/template` `{{if}}` / `{{else}}` blocks driven
   by the combo selectors: `.Type`, `.HTTPFramework`, `.Broker`, `.Database`,
   `.Cache`. Use `repository.go.tmpl` and `config.go.tmpl` as references.
4. Add the basename to the `b1Ready` set in `.claude/hooks/smoke/combos.go`.
5. Move the entry from "Pending" to "Converted" below.
6. Edit the template once to fire the hook. Confirm the smoke runner now
   compiles the affected combos cleanly. Fix template bugs surfaced by the
   build until smoke is green.

## Templates

### Converted (smoke-covered)

- [x] `apperr.go.tmpl` (pure substitution)
- [x] `domain.go.tmpl` (pure substitution)
- [x] `port.go.tmpl` (pure substitution)
- [x] `service.go.tmpl` (pure substitution; revisit if publisher injection is added)
- [x] `subscriber.go.tmpl` (pure substitution)
- [x] `repository.go.tmpl`
- [x] `config.go.tmpl`
- [x] `main_api_nethttp.go.tmpl` (huma adapter via `humago`)
- [x] `main_api_gin.go.tmpl` (huma adapter via `humagin`)
- [x] `main_api_chi.go.tmpl` (huma adapter via `humachi`)
- [x] `main_api_mux.go.tmpl` (huma adapter via `humamux`)
- [x] `main_api_echo.go.tmpl` (huma adapter via `humaecho`)
- [x] `httphandler.go.tmpl` (framework-agnostic huma handler — replaces the 5 framework-specific templates)
- [x] `httphandler_dto.go.tmpl` (huma input/output structs + `Resolve()` runs go-playground/validator)
- [x] `validate.go.tmpl` (shared `var validate = validator.New()`)
- [x] `main_consumer_kafka.go.tmpl`
- [x] `main_consumer_rabbitmq.go.tmpl` (also added `RabbitMQURL` config field)
- [x] `main_consumer_redis.go.tmpl` (added `BrokerRedis*` config fields, fixed missing `ctx :=` decl, `redis.NewConsumer` takes `*goredis.Client` not addr string)
- [x] `main_publisher_kafka.go.tmpl` (rewritten as minimal lifecycle: logger + telemetry + publisher + signal — dropped broken `repository`/`service.New(repo, pub)` calls)
- [x] `main_publisher_rabbitmq.go.tmpl` (same minimal shape; uses `amqp091.Dial` + `rabbitmq.NewPublisher` which returns error)
- [x] `main_publisher_redis.go.tmpl` (same; constructs `*goredis.Client` then `pubsubredis.NewPublisher`)

### Pending

**None.** All 21 templates are B1-ready. Future template edits trigger smoke automatically; failures surface as `hookSpecificOutput.additionalContext` in the next turn.

## Combo coverage

**16/16 combos active.** All 21 templates converted. Coverage breakdown:

Representative 13 (one combo per major axis):
- api: nethttp+postgres+none, nethttp+postgres+redis, gin+postgres+memory, chi+mysql+couchbase, mux+postgres+none, echo+postgres+redis, nethttp+nodb+none
- consumer: kafka+postgres+none, rabbitmq+postgres+redis, redis+postgres+none
- publisher: kafka+nodb+none, rabbitmq+nodb+none, redis+nodb+none

Coverage-extension 3 (paths not exercised by the representative set):
- api+nethttp+mysql+none — mysql driver under nethttp
- consumer+kafka+postgres+memory — memory cache under a consumer
- consumer+rabbitmq+nodb+none — consumer without a database

To add more combos: append to `var combos` in `combos.go`, run smoke against any
template that affects the new combo to confirm it builds. No template changes
needed — the existing `{{if}}` directives cover the full combo space.

Any future template edit fires the smoke runner via the PostToolUse hook in
`.claude/settings.json`; build failures surface in the next turn as
`hookSpecificOutput.additionalContext`.

## Conversion patterns to apply

For each `main_*` and `httphandler_*` template, the conversions typically include:

| Concern | From (current) | To (after conversion) |
|---|---|---|
| DB driver import | hardcoded `gorm.io/driver/postgres` | `{{if eq .Database "gorm-mysql"}}gorm.io/driver/mysql{{else if eq .Database "gorm-postgres"}}gorm.io/driver/postgres{{end}}` |
| DB block | unconditional `db.Open(...)` | wrap in `{{if ne .Database "none"}}…{{end}}` |
| Cache wiring | absent | inject per-backend block from SKILL.md `Cache Backend Wiring` section, gated by `{{if eq .Cache "redis"}}` etc. |
| Hardcoded timeouts (`500*time.Millisecond`) | violates CLAUDE.md | swap to `cfg.DBSlowThreshold` etc. — already exposed in `config.go.tmpl` |
| Repository constructor | `repository.New(gormDB)` | `{{if ne .Cache "none"}}repository.NewCached(gormDB, …){{else}}repository.New(gormDB){{end}}` |
| Validator declaration | missing `var validate = validator.New()` package-level | add at package level; remove unused `validator` import for combos that don't validate |

For framework variants (`main_api_chi.go.tmpl`, etc.), these conversions
happen per-file — each framework has its own router setup that doesn't share
between files.

## Running the smoke runner manually

```
cd .claude/hooks/smoke
go run . -template ../../skills/create-go-app/references/<changed.tmpl>
```

Skip lines go to stderr; failures (build errors) go to stdout. Exit 0 if no
build failures, even when all combos skip.

## Self-test

`bash .claude/hooks/smoke/self_test.sh` validates the runner end-to-end by
deliberately injecting a syntax error into a canary template, asserting the
runner reports it correctly, and restoring the template. Exercises 4 paths:

1. clean template, runner direct → exit 0, no stdout
2. broken template, runner direct → exit 1, "build failed" on stdout
3. clean template, smoke.sh wrapper → exit 0, no stdout
4. broken template, smoke.sh wrapper → exit 0, hookSpecificOutput JSON on stdout

Run after any change to `main.go`, `render.go`, `combos.go`, or `smoke.sh`.
