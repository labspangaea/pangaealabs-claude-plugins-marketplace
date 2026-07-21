---
name: create-go-app
description: Scaffold a production-ready Go application (api, consumer, or publisher) wired to go-peruri-lib. Use this whenever the user says "scaffold a Go service", "create a new Go API", "generate a consumer/publisher", "set up a fresh Go project with go-peruri-lib", "make me an order-service / payment-service / etc.", or any phrasing that implies starting a brand-new Go service from scratch. The skill orchestrates create-go-repository -> create-go-service -> create-go-handler in sequence and adds cmd/, config/, go.mod. For adding a single layer to an existing project, use the focused skills directly instead.
allowed-tools: [bash, read, write, edit, grep, glob, mcp__go-lsp__go_diagnose, AskUserQuestion]
model: sonnet
---

# Skill: create-go-app

Scaffold a production-ready Go application that wires `go-peruri-lib`.

> **Orchestration note**: This skill is a full-scaffold orchestrator. It runs the steps of `/create-go-repository` → `/create-go-service` → `/create-go-handler` in sequence, then generates `cmd/`, `config/`, `go.mod`, `go.sum`. For adding a single layer to an existing project, use the focused skills directly.

## Parameters

| Parameter | Required | Default | Values |
|-----------|----------|---------|--------|
| `type` | **yes** | — | `api` · `consumer` · `publisher` |
| `name` | **yes** | — | kebab-case string |
| `http_framework` | no | `gin` | `nethttp` · `gin` · `chi` · `mux` · `echo` |
| `broker` | no | `kafka` | `kafka` · `rabbitmq` · `redis` |
| `database` | no | `gorm-postgres` | `gorm-postgres` · `gorm-mysql` · `none` |
| `cache` | no | `none` | `none` · `redis` · `memory` · `couchbase` |

## Preflight — run before collecting any inputs

Two preflight checks gate the scaffold. **Both MUST run before Step 1.** Read `${CLAUDE_SKILL_DIR}/references/preflight.md` for the exact bash, decision tables, credential-capture copy, and remediation flows — follow it verbatim.

- **Resolve config store.** Source `${CLAUDE_SKILL_DIR}/../../tools/config.env` (layers `~/.peruri-go-scaffolder/config.json` over the in-repo defaults; env vars win — see `references/config-store.md`). It exports `PERURI_REMOTE_HOST`, `PERURI_REMOTE_PROJECT`, `PERURI_GO_LIB_PATH`, and `PERURI_GO_LIB_MODE` (`git`|`local`) for the steps below.
- **Sync `go-peruri-lib`.** Run `${CLAUDE_SKILL_DIR}/../../tools/sync-go-peruri-lib.sh`; dispatch on the first stdout line (`PERURI_TOKEN_MISSING` / `CLONED` / `UP_TO_DATE` / `UPDATE_AVAILABLE` / `ERROR`). Best-effort — never block scaffolding on a sync failure.
- **`GOPRIVATE` gate.** Run `go env GOPRIVATE` and confirm output contains `$PERURI_REMOTE_HOST` (default `sipgn-git.bgn.go.id`). **Hard gate** — without it `go mod tidy` silently falls back to the public proxy.

---

## Collecting Prerequisites — ask one question at a time

Before generating any files, collect missing inputs sequentially. Ask the next question only after receiving the answer to the current one. Skip any question whose answer was already provided as a parameter.

Each enumerated-choice step uses `AskUserQuestion` so the user sees a structured option list rather than reading parameter values out of a plain prompt. Free-text inputs (service name, entity schema) stay as plain prompts because `AskUserQuestion` is choice-based. The recommended default is always listed first with `(Recommended)` appended so the team's preferred shape is one keystroke away.

**Step 1 — type** (if not supplied):

```
AskUserQuestion({
  question: "What type of service are we scaffolding?",
  header:   "Service type",
  options: [
    { label: "API (Recommended)", description: "HTTP service with huma handlers" },
    { label: "Consumer",          description: "Message-broker consumer" },
    { label: "Publisher",         description: "Message-broker publisher" }
  ]
})
```

**Step 2 — name** (if not supplied) — free-text, plain prompt:

> What is the service name? (kebab-case, e.g. `order-service`)

**Step 3 — http_framework** (if `type=api` and not supplied):

```
AskUserQuestion({
  question: "Which HTTP framework should the API use?",
  header:   "HTTP framework",
  options: [
    { label: "gin (Recommended)", description: "github.com/gin-gonic/gin — the team's most common choice" },
    { label: "nethttp",           description: "Standard library net/http, zero deps" },
    { label: "chi",               description: "github.com/go-chi/chi/v5" },
    { label: "echo",              description: "github.com/labstack/echo/v4" }
  ]
})
```

`mux` (`github.com/gorilla/mux`) is still a valid value — it's reachable via the auto-added "Other" entry that accepts free-text. Only four options fit on screen, so the four most common are surfaced and the long-tail option falls through to free-text.

**Step 4 — broker** (if `type` is `consumer` or `publisher` and not supplied):

```
AskUserQuestion({
  question: "Which message broker should the service use?",
  header:   "Broker",
  options: [
    { label: "Kafka (Recommended)", description: "confluent-kafka-go" },
    { label: "RabbitMQ",            description: "amqp091-go" },
    { label: "Redis",               description: "Redis Streams" }
  ]
})
```

**Step 5 — database** (if `type` is `api` or `consumer` and not supplied):

```
AskUserQuestion({
  question: "Which database backend?",
  header:   "Database",
  options: [
    { label: "PostgreSQL via GORM (Recommended)", description: "gorm-postgres — default for new services" },
    { label: "MySQL via GORM",                    description: "gorm-mysql" },
    { label: "None",                              description: "No persistence layer; skip repository wiring" }
  ]
})
```

**Step 6 — cache** (if `database != none` and not supplied; skip when `database == none`):

```
AskUserQuestion({
  question: "Should the repository have a cache wrapper?",
  header:   "Cache",
  options: [
    { label: "None (Recommended)", description: "Skip cache wiring; direct SQL only" },
    { label: "Redis",              description: "Redis cache backend" },
    { label: "In-memory",          description: "In-process cache (single-pod only)" },
    { label: "Couchbase",          description: "Couchbase cache backend" }
  ]
})
```

**Step 7 — entity schema** (always ask, unless the user already provided it in the invocation message) — free-text, plain prompt:

> Provide the entity schema. Accepted formats below.

### Mapping selected labels → parameter values

When the user picks an option above, the user-friendly label is the surface and the parameter value is what gets written into the PARAMS JSON. Use this mapping:

| Step | Selected label | Parameter value |
|---|---|---|
| 1 | API / Consumer / Publisher | `api` / `consumer` / `publisher` |
| 3 | gin / nethttp / chi / echo / Other(`mux`) | `gin` / `nethttp` / `chi` / `echo` / `mux` |
| 4 | Kafka / RabbitMQ / Redis | `kafka` / `rabbitmq` / `redis` |
| 5 | PostgreSQL via GORM / MySQL via GORM / None | `gorm-postgres` / `gorm-mysql` / `none` |
| 6 | None / Redis / In-memory / Couchbase | `none` / `redis` / `memory` / `couchbase` |

| Item | Default |
|------|---------|
| Git module path prefix | `sipgn-git.bgn.go.id/harry.sitohang` — use silently |
| Go version | `1.26.2` — use silently |

---

## Template Syntax

Templates use Go `text/template` directives. Beyond simple substitution (`{{.Entity}}`, `{{.Module}}`, `{{range .Fields}}`), some templates contain `{{if eq .Cache "redis"}}…{{end}}` blocks that gate sections by parameter selection.

**MUST use the `render-file` tool for every file — never evaluate conditionals mentally.** The tool runs the real Go `text/template` engine, so every `{{if}}` branch is evaluated correctly regardless of nesting depth. See **Template Rendering** below.

The `tools/smoke/` runner uses the same engine and the same `Fixture`/`Params` struct, so any file the render tool produces will also pass the smoke check.

## Schema Input

Accepted formats for the entity schema:

| Format | Example |
|--------|---------|
| JSON example | `{"name": "iPhone 15", "price": 999.99, "in_stock": true}` |
| SQL CREATE TABLE | `CREATE TABLE products (id VARCHAR(36) PRIMARY KEY, name VARCHAR(255) NOT NULL, ...)` |
| Swagger / OpenAPI | `properties:` block from a schema object |
| Postman collection | request body JSON example |

Parse the schema into `{{.Fields}}` (see Template Variables below) before substituting into templates.

### System fields — always injected, never from user schema

| Field | Domain type | GORM model type | GORM tag |
|-------|-------------|-----------------|----------|
| `ID` | `string` | `string` | `gorm:"primaryKey;column:id"` |
| `CreatedAt` | `time.Time` | `int64` | `gorm:"column:created_at;autoCreateTime:milli"` |
| `UpdatedAt` | `time.Time` | `int64` | `gorm:"column:updated_at;autoUpdateTime:milli"` |

Strip these from the parsed field list if the user included them.

### Type mapping

| SQL / JSON / OAS type | Go type |
|-----------------------|---------|
| `VARCHAR`, `TEXT`, `CHAR`, string | `string` |
| `INT`, `BIGINT`, `INTEGER`, number (integer) | `int64` |
| `FLOAT`, `DOUBLE`, `DECIMAL`, number (float) | `float64` |
| `BOOLEAN`, `BOOL`, `TINYINT(1)`, boolean | `bool` |
| `TIMESTAMP`, `DATETIME`, string (date-time) | `time.Time` |
| `UUID` | `string` |

### Nullable fields

If a column allows `NULL` / `nullable: true` / absent from `required` array: prepend `*` to the Go type (e.g. `string` → `*string`).

### `validate` tag assignment

Used internally by FieldDef to drive template conditionals — not emitted as a Go struct tag.

| Condition | Value |
|-----------|-------|
| NOT NULL or in `required` array | `required` |
| `VARCHAR(n)` / `maxLength: n` | `required,max=N` |
| nullable / optional | `` (empty string) |

The templates use `{{if not (isRequired .Validate)}}` to decide whether to add `,omitempty` to the json tag, and `{{if parseMaxLength .Validate}}` to add `maxLength:"N"`. No `validate:"..."` struct tag is ever emitted.

## Template Rendering

**MUST render every file through the tool — do not write template output manually.**

### Build the params JSON once

After collecting all inputs (Step 1–7), assemble the JSON object. Use it for every subsequent render call — do not re-assemble per file.

```bash
SKILL_REFS="${CLAUDE_SKILL_DIR}/references"
RENDER="go run ${CLAUDE_SKILL_DIR}/../../tools/render-file/main.go"

PARAMS=$(cat <<'EOF'
{
  "Name":          "order-service",
  "Module":        "sipgn-git.bgn.go.id/harry.sitohang/order-service",
  "Entity":        "Order",
  "EntityLower":   "order",
  "ApperrBase":    1000,
  "Type":          "api",
  "HTTPFramework": "gin",
  "Broker":        "kafka",
  "Database":      "gorm-postgres",
  "Cache":         "redis",
  "Fields": [
    {"Name":"CustomerID","GoType":"string","JSONName":"customer_id","DBColumn":"customer_id","Validate":"required"},
    {"Name":"Total","GoType":"float64","JSONName":"total","DBColumn":"total","Validate":"required"},
    {"Name":"Note","GoType":"*string","JSONName":"note","DBColumn":"note","Validate":""}
  ]
}
EOF
)
```

### Render each file

```bash
$RENDER -template "$SKILL_REFS/config.go.tmpl"                   -params "$PARAMS" -output config/config.go
$RENDER -template "$SKILL_REFS/domain.go.tmpl"                   -params "$PARAMS" -output internal/domain/order.go
$RENDER -template "$SKILL_REFS/port.go.tmpl"                     -params "$PARAMS" -output internal/port/order.go
$RENDER -template "$SKILL_REFS/port_service.go.tmpl"             -params "$PARAMS" -output internal/port/order_service.go
$RENDER -template "$SKILL_REFS/service.go.tmpl"                  -params "$PARAMS" -output internal/service/order.go
$RENDER -template "$SKILL_REFS/service_stub.go.tmpl"             -params "$PARAMS" -output internal/service/stub/order.go
$RENDER -template "$SKILL_REFS/service_factory_default.go.tmpl"  -params "$PARAMS" -output internal/service/factory_default.go
$RENDER -template "$SKILL_REFS/service_factory_stub.go.tmpl"     -params "$PARAMS" -output internal/service/factory_stub.go
$RENDER -template "$SKILL_REFS/apperr.go.tmpl"                   -params "$PARAMS" -output internal/apperr/order.go
$RENDER -template "$SKILL_REFS/repository.go.tmpl"               -params "$PARAMS" -output internal/adapter/outbound/repository/order.go
$RENDER -template "$SKILL_REFS/httphandler.go.tmpl"              -params "$PARAMS" -output internal/adapter/inbound/httphandler/order.go
$RENDER -template "$SKILL_REFS/httphandler_dto.go.tmpl"          -params "$PARAMS" -output internal/adapter/inbound/httphandler/order_dto.go
$RENDER -template "$SKILL_REFS/main_api_gin.go.tmpl"             -params "$PARAMS" -output cmd/order-service/main.go
$RENDER -template "$SKILL_REFS/health.go.tmpl"                   -params "$PARAMS" -output internal/adapter/inbound/httphandler/health.go
$RENDER -template "$SKILL_REFS/docker-compose.yml.tmpl"          -params "$PARAMS" -output docker-compose.yml
$RENDER -template "$SKILL_REFS/.env.tmpl"                        -params "$PARAMS" -output .env
$RENDER -template "$SKILL_REFS/.gitignore.tmpl"                  -params "$PARAMS" -output .gitignore
$RENDER -template "$SKILL_REFS/Dockerfile.tmpl"                  -params "$PARAMS" -output Dockerfile
$RENDER -template "$SKILL_REFS/seed.go.tmpl"                     -params "$PARAMS" -output cmd/seed/main.go
```

### Custom template functions available

The render-file tool registers extra functions used by the dev-env templates:

| Function | Signature | Used in |
|----------|-----------|---------|
| `seq` | `seq(n int) []int` → `[0..n-1]` | `seed.go.tmpl` — `{{range $i, $_ := (seq 25)}}` |
| `seedValue` | `seedValue(goType string, idx int) string` | `seed.go.tmpl` — type-appropriate placeholder |
| `hasFieldType` | `hasFieldType(goType string, fields []FieldDef) bool` | `seed.go.tmpl` — conditional `time` import |
| `hasNullableField` | `hasNullableField(fields []FieldDef) bool` | `seed.go.tmpl` — conditional `ptr` import (only emitted when ≥1 nullable/`*T` field, since `seedValue` only references `ptr.Of(...)` for those) |
| `dbOpen` | `dbOpen(database string) string` | `config.go.tmpl` — `postgres.Open` vs `mysql.Open` |
| `isRequired` | `isRequired(validate string) bool` | `httphandler_dto.go.tmpl` — `,omitempty` on optional fields |
| `parseMaxLength` | `parseMaxLength(validate string) int` | `httphandler_dto.go.tmpl` — `maxLength:"N"` struct tag |

---

## Output

Generate `{name}/` as a **sibling directory to `go-peruri-lib`** (not inside it). If the directory already exists, **MUST ask before overwriting**.

---

## Architecture

Hexagonal (Ports & Adapters):

```
cmd/{name}/main.go                          — composition root, wires all deps
config/config.go                            — env-based config
internal/domain/{entity}.go                 — business types, errors, value objects
internal/port/
  {entity}.go                               — {Entity}Repository port (driven side)
  {entity}_service.go                       — (api) {Entity}Service port — handler contract
internal/service/
  {entity}.go                               — real use cases; imports port only
  stub/{entity}.go                          — (api) //go:build stub; canned-response stub
  factory_default.go                        — (api) //go:build !stub; returns real service
  factory_stub.go                           — (api) //go:build stub; switches on cfg.ServiceBackend
internal/adapter/inbound/
  httphandler/{entity}.go                   — (api) huma handler funcs
  httphandler/{entity}_dto.go               — (api) huma input/output structs, huma-native validation
  subscriber/handler.go                     — (consumer) message handlers
internal/adapter/outbound/
  repository/{entity}.go                   — DB implementation of port interface
  publisher/publisher.go                   — (publisher) message publisher
  client/                                  — outbound HTTP clients
```

### SOLID Constraints

| Principle | Constraint | Do | Don't |
|-----------|-----------|-----|-------|
| SRP | Single responsibility per layer | handlers serialize HTTP only | handlers calling `db.Query(...)` |
| OCP | Extend by adding files | new `internal/service/refund.go` | editing existing switch blocks |
| DIP | `service/` imports `port/` only | `port.OrderRepository` | `import ".../adapter/repository"` in service |
| ISP | Port interfaces 1–3 methods | split `OrderReader` / `OrderWriter` | one interface with 10 methods |
| LSP | All port impls substitutable | swap Redis cache for Nop in tests | impl that panics on unsupported method |

---

## Wiring Rules

**Before generating `cmd/{name}/main.go` and the surrounding `internal/*` files, read `${CLAUDE_SKILL_DIR}/references/wiring-rules.md` and apply every rule.** The full MUST / MUST NOT table (Foundational / HTTP / Error codes / Repository / Service / Cross-cutting) lives there; templates in `references/*.tmpl` already conform. Top three most-violated rules:

- **HTTP error dispatch** (MUST): `return nil, err` from huma handlers — never serialize errors yourself.
- **No domain error sentinels** (MUST NOT): no `var ErrNotFound = errors.New(...)` in `domain/`. All named errors live in `internal/apperr/{{.EntityLower}}.go` as `CodeErrEnum` constants.
- **No hardcoded timeouts** (MUST NOT): no `time.Second` / `time.Millisecond` literals in `main.go` — timeouts come from `cfg.*` via `envDurationOr`.

---

## Cache Backend Wiring (only when `cache != none`)

When `cache != none`, the per-backend `main.go` block is injected between the DB-open call and `repository.NewCached`. The exact code recipes per backend (`redis` / `memory` / `couchbase`) and the `cache=none` fallthrough live at `${CLAUDE_SKILL_DIR}/references/cache-backends.md` — read that file when emitting the cache wiring.

The same recipes are also rendered by `/peruri-go-scaffolder:create-go-repository` Step 7 for the single-repository case; keep the reference file in sync if either changes.

---

## File Generation — Decision Table

| `type` | `database` | Files generated |
|--------|-----------|----------------|
| `api` | `gorm-postgres` or `gorm-mysql` | all + `repository/`, `apperr/` |
| `api` | `none` | all except `repository/`; `apperr/` included |
| `consumer` | `gorm-postgres` or `gorm-mysql` | all + `repository/`, `apperr/`, `subscriber/` |
| `consumer` | `none` | all except `repository/` and `apperr/`; `subscriber/` included |
| `publisher` | any | all + `publisher/`; no `repository/` |

## File Generation Templates

`{http_framework}` and `{broker}` substituted with parameter value.

| type | Output path | Template | Condition |
|------|-------------|----------|-----------|
| all | `config/config.go` | `config.go.tmpl` | — |
| all | `internal/domain/{entity}.go` | `domain.go.tmpl` | — |
| all | `internal/port/{entity}.go` | `port.go.tmpl` | — |
| `api` | `internal/port/{entity}_service.go` | `port_service.go.tmpl` | — |
| all | `internal/service/{entity}.go` | `service.go.tmpl` | — |
| `api` | `internal/service/stub/{entity}.go` | `service_stub.go.tmpl` | — |
| `api` | `internal/service/factory_default.go` | `service_factory_default.go.tmpl` | — |
| `api` | `internal/service/factory_stub.go` | `service_factory_stub.go.tmpl` | — |
| `api` | `cmd/{name}/main.go` | `main_api_{http_framework}.go.tmpl` | — |
| `api` | `internal/adapter/inbound/httphandler/{entity}.go` | `httphandler.go.tmpl` | — |
| `api` | `internal/adapter/inbound/httphandler/{entity}_dto.go` | `httphandler_dto.go.tmpl` | — |
| `api` | `internal/adapter/outbound/repository/{entity}.go` | `repository.go.tmpl` | database ≠ `none` |
| `api` | `internal/apperr/{entity}.go` | `apperr.go.tmpl` | — |
| `consumer` | `internal/apperr/{entity}.go` | `apperr.go.tmpl` | database ≠ `none` (repository.go.tmpl references `apperr.ErrXxxNotFound`) |
| `consumer` | `cmd/{name}/main.go` | `main_consumer_{broker}.go.tmpl` | — |
| `consumer` | `internal/adapter/inbound/subscriber/handler.go` | `subscriber.go.tmpl` | — |
| `consumer` | `internal/adapter/outbound/repository/{entity}.go` | `repository.go.tmpl` | database ≠ `none` |
| `publisher` | `cmd/{name}/main.go` | `main_publisher_{broker}.go.tmpl` | — |
| `publisher` | `internal/adapter/outbound/publisher/publisher.go` | *(write inline)* | — |
| `api` | `internal/adapter/inbound/httphandler/health.go` | `health.go.tmpl` | — |
| all | `Dockerfile` | `Dockerfile.tmpl` | — |
| all | `docker-compose.yml` | `docker-compose.yml.tmpl` | — |
| all | `.env` | `.env.tmpl` | — |
| all | `.gitignore` | `.gitignore.tmpl` | — |
| `api`, `consumer` | `cmd/seed/main.go` | `seed.go.tmpl` | database ≠ `none` |

---

## Template Variables

| Variable | Derived from | Example (`name=order-service`) |
|----------|-------------|-------------------------------|
| `{{.Name}}` | `name` param | `order-service` |
| `{{.Module}}` | module prefix + `name` | `sipgn-git.bgn.go.id/harry.sitohang/order-service` |
| `{{.Entity}}` | `name` → PascalCase singular | `Order` |
| `{{.EntityLower}}` | `{{.Entity}}` → lowercase | `order` |
| `{{.Fields}}` | parsed from user schema (see Schema Input) | `[]FieldDef` — each has `.Name`, `.GoType`, `.JSONName`, `.DBColumn`, `.Validate` |

### FieldDef attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| `.Name` | PascalCase Go identifier | `ProductCode`, `UserID` |
| `.GoType` | Go type string | `string`, `int64`, `*int64`, `bool`, `float64`, `time.Time` |
| `.JSONName` | snake_case json/query tag | `product_code` |
| `.DBColumn` | snake_case gorm column | `product_code` |
| `.Validate` | constraint descriptor used by template functions (`isRequired`, `parseMaxLength`) | `required`, `required,max=255`, `` (empty = optional) |

Templates use `{{range .Fields}}` to iterate. Use `{{if eq .GoType "string"}}` to conditionally include string-only filters.

---

## Code Style

Local style + error-wrapping rules baked into the templates live at `${CLAUDE_SKILL_DIR}/references/code-style.md`. Read it before authoring or hand-tweaking generated Go files. The wider cross-cutting Go rulebook is in `peruri-code-standard/references/go.md`.

---

## Post-Generation

```bash
go mod init {module_path}

# Lib import mode (config-store libMode / $PERURI_GO_LIB_MODE, default git):
#   local → wire the build to the local go-peruri-lib checkout via a replace directive.
#   git   → skip; go mod tidy fetches from GitLab over GOPRIVATE (default).
if [ "${PERURI_GO_LIB_MODE:-git}" = "local" ]; then
  go mod edit -replace "${PERURI_GO_MODULE}=${PERURI_GO_LIB_PATH}"
fi

go mod tidy       # GOPRIVATE confirmed in Preflight; git mode fetches go-peruri-lib from GitLab, local mode resolves the replace.
gofmt -w .        # MUST run — templates emit hand-aligned struct fields; without this step every editor save produces noisy diffs.

# Verify both build modes compile clean:
go build ./...               # production — stub package excluded
go build -tags=stub ./...    # stub-mode — both factory variants visible
```

### Stub mode — FE/BE parallel development

Default `.env` ships `SERVICE_BACKEND=stub`. Boot the API without postgres / mysql / redis and serve canned, shape-correct responses (huma OpenAPI + Stoplight Elements UI live at `/docs`):

```bash
go run -tags=stub ./cmd/{name}    # FE points at http://localhost:8080/docs
```

When backend business logic is ready, switch to the real service:

```bash
docker compose up -d postgres redis    # whatever the real service needs
echo "SERVICE_BACKEND=real" >> .env
go run -tags=stub ./cmd/{name}         # OR: go run ./cmd/{name}  (always real, no tag)
```

### Removing the stub once business logic is final

The stub is structurally quarantined for mechanical removal:

- **Soft removal (keep code, never run):** Set `SERVICE_BACKEND=real` in prod `.env`. Build without `-tags=stub` — the stub package isn't linked; the env var is ignored. Zero code change.
- **Hard removal (delete code):** (1) `rm -rf internal/service/stub/`; (2) `rm internal/service/factory_stub.go`; (3) delete `ServiceBackend` from `config/config.go` (struct + Load); (4) delete `SERVICE_BACKEND=...` from `.env`; (5) (optional) inline `return New(repo)` from `factory_default.go` into `cmd/{name}/main.go` and delete `factory_default.go`. After step 4 the project compiles identically to a pre-stub scaffold.

**MUST**: After writing each `.go` file, run `mcp__go-lsp__go_diagnose` before reporting done.

### Dev environment bootstrap

Once `go build` passes, walk the user through bringing the stack up with Docker Compose, seeding the DB, and hitting the local endpoints. The exact command sequence (image build → health-wait → seed → smoke `/healthz`) plus the host-vs-container DSN explanation is in `${CLAUDE_SKILL_DIR}/references/dev-bootstrap.md`.

---

## Telemetry posture & OpenAPI

Both are env-driven, runtime-configurable, and rarely require code changes. Read these reference files when wiring the matching parts of `main.go` / `httphandler/`:

- **Telemetry (env-driven OTLP exporter posture, log bridge, common SaaS configs):** `${CLAUDE_SKILL_DIR}/references/telemetry.md`
- **OpenAPI / Swagger UI (huma endpoints, validation rules, response envelope):** `${CLAUDE_SKILL_DIR}/references/openapi.md`

---

## Example

```bash
/create-go-app type=api name=order-service
```

```
order-service/
├── cmd/order-service/main.go
├── config/config.go
├── internal/
│   ├── domain/order.go
│   ├── port/
│   │   ├── order.go              # OrderRepository (driven port)
│   │   └── order_service.go      # OrderService (handler-facing port)
│   ├── service/
│   │   ├── order.go              # real service
│   │   ├── factory_default.go    # //go:build !stub  — wires real
│   │   ├── factory_stub.go       # //go:build stub   — switches on env
│   │   └── stub/order.go         # //go:build stub   — canned responses
│   ├── apperr/order.go
│   └── adapter/
│       ├── inbound/httphandler/order.go
│       ├── inbound/httphandler/order_dto.go
│       ├── inbound/httphandler/health.go
│       └── outbound/repository/order.go
├── go.mod
└── go.sum
```
