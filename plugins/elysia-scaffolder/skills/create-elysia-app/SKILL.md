---
name: create-elysia-app
description: Scaffold a production-ready ElysiaJS/Bun application (api, consumer, or publisher) wired to @labspangaea/ts-lib. Use this whenever the user says "scaffold an Elysia service", "create a new Bun API", "generate a consumer/publisher", "set up a fresh Elysia project with @labspangaea/ts-lib", "make me an order-service / payment-service / etc.", or any phrasing that implies starting a brand-new Bun/Elysia service from scratch. The skill orchestrates create-elysia-repository -> create-elysia-service -> create-elysia-handler in sequence and adds src/index.ts, config, package.json, tsconfig, drizzle config. For adding a single layer to an existing project, use the focused skills directly instead.
allowed-tools: [bash, read, write, edit, grep, glob, mcp__ts-lsp__ts_diagnose, AskUserQuestion]
model: inherit
---

# Skill: create-elysia-app

Scaffold a production-ready ElysiaJS application on Bun that wires `@labspangaea/ts-lib`
(the TypeScript port of `go-lib`).

> **Orchestration note**: This skill is a full-scaffold orchestrator. It runs the steps of
> `/create-elysia-repository` → `/create-elysia-service` → `/create-elysia-handler` in sequence,
> then generates `src/index.ts` (composition root), `config`, `package.json`, `tsconfig.json`,
> `drizzle.config.ts`. For adding a single layer to an existing project, use the focused skills directly.

> **Architecture posture (hybrid)**: The generated app keeps a strict **hexagonal core**
> (domain / port / service / repository / apperr) but the inbound adapter is a **thin, idiomatic
> Elysia controller** — not a port-hidden handler. This preserves Elysia's end-to-end TypeBox
> inference + OpenAPI autogen while keeping business logic decoupled from HTTP (DIP). This is a
> deliberate, documented divergence from the Go plugin's pure ports-and-adapters inbound side.

## Parameters

| Parameter | Required | Default | Values |
|-----------|----------|---------|--------|
| `type` | **yes** | — | `api` · `consumer` · `publisher` |
| `name` | **yes** | — | kebab-case string |
| `database` | no | `drizzle-postgres` | `drizzle-postgres` · `drizzle-mysql` · `none` |
| `cache` | no | `none` | `none` · `redis` · `memory` · `couchbase` |
| `broker` | no | `kafka` | `kafka` · `rabbitmq` · `redis` |

> **No `http_framework` axis.** Elysia *is* the framework, so the Go plugin's nethttp/gin/chi/mux/echo
> parameter does not exist here. The matrix is `type × database × cache × broker`.

## Preflight — run before collecting any inputs

Three preflight checks gate the scaffold. **All MUST run before Step 1.** Read
`${CLAUDE_SKILL_DIR}/references/preflight.md` for the exact bash, decision tables, and remediation —
follow it verbatim.

- **Bun present.** `bun --version` must succeed (Bun 1.1+). Hard gate — the whole toolchain is Bun.
- **`@labspangaea/ts-lib` is a public npm package.** The generated `package.json` depends on it
  directly (`"@labspangaea/ts-lib": "^0.1.0"`) and `bun install` fetches it from the public registry —
  no registry token, no `.npmrc` auth, no `file:` sibling path, no config store. Only a network
  connection is needed (best-effort check; never block scaffolding on a registry hiccup).
- **`mcp__ts-lsp__ts_diagnose` available.** The skill calls it after every file write to catch type
  errors before reporting done (the analog of the Go plugin's `go_diagnose` gate).

---

## Collecting Prerequisites — ask one question at a time

Before generating any files, collect missing inputs sequentially via `AskUserQuestion` (one structured
question at a time). Skip any question already answered as a parameter. The recommended default is
listed first with `(Recommended)` appended.

**Step 1 — type** (if not supplied):

```
AskUserQuestion({
  question: "What type of service are we scaffolding?",
  header:   "Service type",
  options: [
    { label: "API (Recommended)", description: "HTTP service with Elysia + TypeBox handlers" },
    { label: "Consumer",          description: "Message-broker consumer" },
    { label: "Publisher",         description: "Message-broker publisher" }
  ]
})
```

**Step 2 — name** (if not supplied) — free-text, plain prompt:

> What is the service name? (kebab-case, e.g. `order-service`)

**Step 3 — database** (if `type` is `api` or `consumer` and not supplied):

```
AskUserQuestion({
  question: "Which database backend?",
  header:   "Database",
  options: [
    { label: "PostgreSQL via Drizzle (Recommended)", description: "drizzle-postgres — default for new services" },
    { label: "MySQL via Drizzle",                    description: "drizzle-mysql" },
    { label: "None",                                 description: "No persistence layer; skip repository wiring" }
  ]
})
```

**Step 4 — cache** (if `database != none` and not supplied; skip when `database == none`):

```
AskUserQuestion({
  question: "Should the repository have a cache wrapper?",
  header:   "Cache",
  options: [
    { label: "None (Recommended)", description: "Skip cache wiring; direct SQL only" },
    { label: "Redis",              description: "Redis cache backend (ioredis)" },
    { label: "In-memory",          description: "In-process LRU cache (single-pod only)" },
    { label: "Couchbase",          description: "Couchbase cache backend" }
  ]
})
```

**Step 5 — broker** (if `type` is `consumer` or `publisher` and not supplied):

```
AskUserQuestion({
  question: "Which message broker should the service use?",
  header:   "Broker",
  options: [
    { label: "Kafka (Recommended)", description: "kafkajs" },
    { label: "RabbitMQ",            description: "amqplib" },
    { label: "Redis",               description: "Redis pub/sub via ioredis" }
  ]
})
```

**Step 6 — entity schema** (always ask, unless already provided) — free-text, plain prompt:

> Provide the entity schema. Accepted formats below.

### Mapping selected labels → parameter values

| Step | Selected label | Parameter value |
|---|---|---|
| 1 | API / Consumer / Publisher | `api` / `consumer` / `publisher` |
| 3 | PostgreSQL via Drizzle / MySQL via Drizzle / None | `drizzle-postgres` / `drizzle-mysql` / `none` |
| 4 | None / Redis / In-memory / Couchbase | `none` / `redis` / `memory` / `couchbase` |
| 5 | Kafka / RabbitMQ / Redis | `kafka` / `rabbitmq` / `redis` |

| Item | Default |
|------|---------|
| npm scope prefix | `@labspangaea` — use silently for the app's own package name unless told otherwise |
| Bun version target | latest stable — use silently |

---

## Template Syntax

Templates are rendered by the Bun/TS `render-file` tool (`${CLAUDE_SKILL_DIR}/../../tools/render-file/`),
which runs a real template engine over `*.tmpl` files. Beyond simple substitution (`{{Entity}}`,
`{{Module}}`, `{{#each Fields}}`) some templates contain `{{#if (eq Cache "redis")}}…{{/if}}` blocks
that gate sections by parameter selection.

**MUST render every file through the tool — never evaluate conditionals mentally.** The tool evaluates
every branch deterministically regardless of nesting depth. See **Template Rendering** below. The
`tools/smoke/` runner uses the same engine and the same `Params` shape, so any file the render tool
produces will also pass the smoke (type-check) gate.

## Schema Input

Accepted formats for the entity schema:

| Format | Example |
|--------|---------|
| JSON example | `{"name": "iPhone 15", "price": 999.99, "in_stock": true}` |
| SQL CREATE TABLE | `CREATE TABLE products (id VARCHAR(36) PRIMARY KEY, name VARCHAR(255) NOT NULL, ...)` |
| Swagger / OpenAPI | `properties:` block from a schema object |
| Postman collection | request body JSON example |

Parse the schema into `Fields` (see Template Variables) before rendering.

### System fields — always injected, never from user schema

| Field | Domain type | Drizzle column | Wire (JSON) |
|-------|-------------|----------------|-------------|
| `id` | `string` | `varchar/text` primary key | string |
| `createdAt` | `Date` | `bigint` (epoch ms, set on insert) | ISO date-time string |
| `updatedAt` | `Date` | `bigint` (epoch ms, set on update) | ISO date-time string |

Strip these from the parsed field list if the user included them. (Epoch-ms `bigint` storage mirrors
the Go lib's `autoCreateTime:milli` / `int64` columns; the repository maps `bigint ↔ Date`.)

### Type mapping

| SQL / JSON / OAS type | TS domain type | TypeBox (DTO) | Drizzle column |
|-----------------------|----------------|---------------|----------------|
| `VARCHAR`, `TEXT`, `CHAR`, string | `string` | `t.String()` | `varchar` / `text` |
| `INT`, `INTEGER`, number (integer) | `number` | `t.Integer()` | `integer` |
| `BIGINT` | `number` | `t.Integer()` | `bigint({ mode: 'number' })` |
| `FLOAT`, `DOUBLE`, `DECIMAL`, number (float) | `number` | `t.Number()` | `doublePrecision` / `decimal` |
| `BOOLEAN`, `BOOL`, `TINYINT(1)`, boolean | `boolean` | `t.Boolean()` | `boolean` |
| `TIMESTAMP`, `DATETIME`, string (date-time) | `Date` | `t.String({ format: 'date-time' })` | `bigint({ mode: 'number' })` |
| `UUID` | `string` | `t.String({ format: 'uuid' })` | `varchar` / `uuid` |

### Nullable fields

If a column allows `NULL` / `nullable: true` / absent from `required`: the TS type becomes `T | null`,
the TypeBox schema is wrapped `t.Optional(t.Union([..., t.Null()]))`, and the Drizzle column drops
`.notNull()`.

### `validate` descriptor

Used internally by FieldDef to drive template conditionals — TypeBox derives both runtime validation
and the OpenAPI schema, so no separate validator runs.

| Condition | Value |
|-----------|-------|
| NOT NULL or in `required` array | `required` |
| `VARCHAR(n)` / `maxLength: n` | `required,max=N` → `t.String({ maxLength: N })` |
| nullable / optional | `` (empty string) → field is `t.Optional(...)` |

## Template Rendering

**MUST render every file through the tool — do not write template output manually.**

### Build the params JSON once

After collecting all inputs (Step 1–6), assemble the JSON object and reuse it for every render call.
The generated `package.json` depends on the public `@labspangaea/ts-lib` at a fixed version
(`"@labspangaea/ts-lib": "^0.1.0"`, hardcoded in `package.json.tmpl`) — nothing to resolve or pass in.

```bash
SKILL_REFS="${CLAUDE_SKILL_DIR}/references"
RENDER="bun ${CLAUDE_SKILL_DIR}/../../tools/render-file/index.ts"

PARAMS=$(cat <<'EOF'
{
  "Name":        "order-service",
  "Module":      "@labspangaea/order-service",
  "Entity":      "Order",
  "EntityLower": "order",
  "ApperrBase":  1000,
  "Type":        "api",
  "Broker":      "kafka",
  "Database":    "drizzle-postgres",
  "Cache":       "redis",
  "Fields": [
    {"Name":"customerId","GoType":"string","JSONName":"customer_id","DBColumn":"customer_id","Validate":"required"},
    {"Name":"total","GoType":"number","JSONName":"total","DBColumn":"total","Validate":"required"},
    {"Name":"note","GoType":"string | null","JSONName":"note","DBColumn":"note","Validate":""}
  ]
}
EOF
)
```

### Render each file

```bash
$RENDER -template "$SKILL_REFS/config.ts.tmpl"            -params "$PARAMS" -output config/config.ts
$RENDER -template "$SKILL_REFS/domain.ts.tmpl"           -params "$PARAMS" -output src/domain/order.ts
$RENDER -template "$SKILL_REFS/port.ts.tmpl"             -params "$PARAMS" -output src/port/order.ts
$RENDER -template "$SKILL_REFS/port_service.ts.tmpl"     -params "$PARAMS" -output src/port/order-service.ts
$RENDER -template "$SKILL_REFS/service.ts.tmpl"          -params "$PARAMS" -output src/service/order.ts
$RENDER -template "$SKILL_REFS/service_stub.ts.tmpl"     -params "$PARAMS" -output src/service/stub/order.ts
$RENDER -template "$SKILL_REFS/service_factory.ts.tmpl"  -params "$PARAMS" -output src/service/factory.ts
$RENDER -template "$SKILL_REFS/apperr.ts.tmpl"           -params "$PARAMS" -output src/apperr/order.ts
$RENDER -template "$SKILL_REFS/schema.ts.tmpl"           -params "$PARAMS" -output src/db/schema/order.ts
$RENDER -template "$SKILL_REFS/repository.ts.tmpl"       -params "$PARAMS" -output src/adapter/outbound/repository/order.ts
$RENDER -template "$SKILL_REFS/controller.ts.tmpl"       -params "$PARAMS" -output src/adapter/inbound/http/order.ts
$RENDER -template "$SKILL_REFS/dto.ts.tmpl"              -params "$PARAMS" -output src/adapter/inbound/http/order.dto.ts
$RENDER -template "$SKILL_REFS/health.ts.tmpl"           -params "$PARAMS" -output src/adapter/inbound/http/health.ts
$RENDER -template "$SKILL_REFS/index_api.ts.tmpl"        -params "$PARAMS" -output src/index.ts
$RENDER -template "$SKILL_REFS/seed.ts.tmpl"             -params "$PARAMS" -output src/cmd/seed.ts
$RENDER -template "$SKILL_REFS/drizzle.config.ts.tmpl"   -params "$PARAMS" -output drizzle.config.ts
$RENDER -template "$SKILL_REFS/package.json.tmpl"        -params "$PARAMS" -output package.json
$RENDER -template "$SKILL_REFS/tsconfig.json.tmpl"       -params "$PARAMS" -output tsconfig.json
$RENDER -template "$SKILL_REFS/Dockerfile.tmpl"          -params "$PARAMS" -output Dockerfile
$RENDER -template "$SKILL_REFS/docker-compose.yml.tmpl"  -params "$PARAMS" -output docker-compose.yml
$RENDER -template "$SKILL_REFS/env.tmpl"                 -params "$PARAMS" -output .env
$RENDER -template "$SKILL_REFS/gitignore.tmpl"           -params "$PARAMS" -output .gitignore
$RENDER -template "$SKILL_REFS/README.md.tmpl"           -params "$PARAMS" -output README.md
$RENDER -template "$SKILL_REFS/CLAUDE.md.tmpl"           -params "$PARAMS" -output CLAUDE.md
```

`README.md` (architecture + request→response flow diagram + endpoints) and `CLAUDE.md`
(project-level guidance: dependency rule, conventions, gotchas) are generated for **every**
service type — they adapt to `type`/`database`/`cache`/`broker`.

For `type=consumer`: render `index_consumer.ts.tmpl` → `src/index.ts` (broker-conditional inside)
and `subscriber.ts.tmpl` → `src/adapter/inbound/subscriber/handler.ts`; drop the controller/dto/
health/stub/factory. For `type=publisher`: render `index_publisher.ts.tmpl` → `src/index.ts` and
`publisher.ts.tmpl` → `src/adapter/outbound/publisher/publisher.ts`; drop the repository/schema/
apperr/service/port (publisher keeps only domain + config + the publisher adapter).

### Custom template functions

Registered by the render-file tool (mirrors the Go renderer's funcs):

| Function | Purpose |
|----------|---------|
| `seq n` | `[0..n-1]` — used by `seed.ts.tmpl` |
| `seedValue goType idx` | type-appropriate placeholder (string/number/boolean/Date, null-wrapped for nullable) |
| `hasFieldType goType Fields` | conditional import in seed |
| `hasNullableField Fields` | conditional null handling |
| `isRequired validate` | drives `t.Optional(...)` vs required in DTO |
| `parseMaxLength validate` | `t.String({ maxLength: N })` |
| `dbDialect database` | `pg` vs `mysql` Drizzle dialect import |

---

## Output

Generate `{name}/` as a standalone project at a path the user names (`@labspangaea/ts-lib` is a
public dependency, so no workspace or sibling layout is required). If the directory already exists,
**MUST ask before overwriting**.

---

## Architecture

Hexagonal core + thin Elysia controller:

```
src/index.ts                                  -- composition root: Elysia app, ALS, OTel, middleware, graceful stop
config/config.ts                              -- env-driven config (Bun.env)
src/domain/{entity}.ts                        -- business types
src/port/{entity}.ts                          -- {Entity}Repository interface (driven port)
src/port/{entity}-service.ts                  -- (api) {Entity}Service interface (controller contract)
src/service/{entity}.ts                       -- real use-cases; `satisfies {Entity}Service`
src/service/stub/{entity}.ts                  -- (api) canned-response stub (tree-shaken out of prod)
src/service/factory.ts                        -- SERVICE_BACKEND switch (stub branch dead-code-eliminated in prod)
src/apperr/{entity}.ts                        -- CodeErr enum + registry, base offset
src/db/schema/{entity}.ts                     -- Drizzle table schema
src/adapter/inbound/http/{entity}.ts          -- (api) THIN Elysia controller: routes + TypeBox
src/adapter/inbound/http/{entity}.dto.ts      -- (api) TypeBox input/output schemas
src/adapter/inbound/subscriber/handler.ts     -- (consumer) message handler
src/adapter/outbound/repository/{entity}.ts   -- Drizzle impl of the port (BaseRepo/CachedRepo equiv)
src/adapter/outbound/publisher/publisher.ts   -- (publisher) message publisher
```

### SOLID Constraints

| Principle | Constraint | Do | Don't |
|-----------|-----------|-----|-------|
| SRP | one responsibility per layer | controller serializes HTTP only | controller running `db.select(...)` |
| OCP | extend by adding files | new `src/service/refund.ts` | editing existing switch blocks |
| DIP | `service/` imports `port/` only | `OrderRepository` interface | importing the Drizzle repo in the service |
| ISP | port interfaces 1–3 methods | split `OrderReader` / `OrderWriter` | one interface with 10 methods |
| LSP | all port impls substitutable | swap Redis cache for `nop()` in tests | impl that throws on an unsupported method |

---

## Wiring Rules

**Before generating `src/index.ts` and the surrounding `src/*` files, read
`${CLAUDE_SKILL_DIR}/references/wiring-rules.md` and apply every rule.** Top three most-violated:

- **HTTP error dispatch** (MUST): `throw new ApiError(...)` from the controller; the Elysia `onError`
  hook (provided by `@labspangaea/ts-lib/server`) renders the envelope and sets the status. Never build error
  JSON by hand.
- **No domain error sentinels** (MUST NOT): no `export const ErrNotFound = ...` in `domain/`. All named
  errors live in `src/apperr/{entity}.ts` as `CodeErr` registry entries.
- **No hardcoded timeouts** (MUST NOT): no literal `5000` / `30_000` in `index.ts` — timeouts come from
  `cfg.*` via `envDurationMs`.

---

## Cache Backend Wiring (only when `cache != none`)

When `cache != none`, the per-backend block is injected between the Drizzle connection and the
`makeCachedRepository(...)` call. Recipes per backend (`redis` / `memory` / `couchbase`) and the
`cache=none` fallthrough live at `${CLAUDE_SKILL_DIR}/references/cache-backends.md` — read it when
emitting cache wiring. The cache value type is the **row type** (Drizzle model), and the key prefix is
passed to `makeCachedRepository` — do **not** also set a prefix on the backend (double-prefix).

---

## File Generation — Decision Table

| `type` | `database` | Files generated |
|--------|-----------|----------------|
| `api` | `drizzle-*` | all + `repository/`, `schema/`, `apperr/` |
| `api` | `none` | all except `repository/` + `schema/`; `apperr/` included |
| `consumer` | `drizzle-*` | all + `repository/`, `schema/`, `apperr/`, `subscriber/` |
| `consumer` | `none` | all except `repository/`/`schema/`/`apperr/`; `subscriber/` included |
| `publisher` | any | all + `publisher/`; no `repository/`/controller |

---

## Template Variables

| Variable | Derived from | Example (`name=order-service`) |
|----------|-------------|-------------------------------|
| `{{Name}}` | `name` param | `order-service` |
| `{{Module}}` | `@labspangaea/` + `name` | `@labspangaea/order-service` |
| `{{Entity}}` | `name` → PascalCase singular | `Order` |
| `{{EntityLower}}` | `{{Entity}}` → lowercase | `order` |
| `{{Fields}}` | parsed from schema | `FieldDef[]` — `.Name`, `.GoType`, `.JSONName`, `.DBColumn`, `.Validate` |

`FieldDef.GoType` is the TS type string (`string`, `number`, `boolean`, `Date`, or `T | null`). The
name is kept as `GoType` so the Params shape stays identical to the Go renderer's `FieldDef` (one less
thing to diverge).

---

## Code Style

Local style + error-wrapping rules baked into the templates live at
`${CLAUDE_SKILL_DIR}/references/code-style.md`. Read it before authoring or hand-tweaking generated TS.

---

## Post-Generation

```bash
bun install                       # fetches @labspangaea/ts-lib from the public npm registry
bunx drizzle-kit generate         # generate the SQL migration from the schema (or `drizzle-kit push` for dev)
bunx tsc --noEmit                 # type-check — MUST pass clean
bun build ./src/index.ts --target bun --outdir dist        # production build (stub tree-shaken out)
bun build ./src/index.ts --target bun --define SERVICE_STUB=true --outdir dist-stub   # stub-enabled build
```

### Stub mode — FE/BE parallel development

Default `.env` ships `SERVICE_BACKEND=stub`. Boot the API without postgres / mysql / redis and serve
canned, shape-correct responses (OpenAPI + Scalar UI at `/docs`):

```bash
SERVICE_BACKEND=stub bun run src/index.ts    # FE points at http://localhost:8080/docs
```

When backend business logic is ready, switch to the real service:

```bash
docker compose up -d postgres redis
echo "SERVICE_BACKEND=real" >> .env
bun run src/index.ts
```

### Stub mode — the build-time guarantee

The factory uses a compile-time constant so the **production binary excludes the stub** (Go build-tag
parity, via dead-code elimination):

- `src/service/factory.ts` reads `declare const SERVICE_STUB: boolean` (defaulted `false`).
- Prod `bun build` (no `--define SERVICE_STUB=true`) ⇒ the `if (SERVICE_STUB)` branch is statically
  `false` ⇒ Bun's bundler tree-shakes the `import('./stub/...')` and the stub module is **not linked**.
- Stub build (`--define SERVICE_STUB=true`) keeps both; `SERVICE_BACKEND` then chooses at boot.

**Removing the stub once business logic is final:** (1) `rm -rf src/service/stub/`; (2) delete the
`SERVICE_STUB` branch from `factory.ts`; (3) delete `SERVICE_BACKEND` from `config.ts` + `.env`. After
that the project compiles identically to a pre-stub scaffold.

**MUST**: After writing each `.ts` file, run `mcp__ts-lsp__ts_diagnose` before reporting done.

### Dev environment bootstrap

Once `tsc --noEmit` passes, walk the user through bringing the stack up: `docker compose up -d --wait`,
`bun run src/cmd/seed.ts`, then `curl localhost:8080/healthz`. The exact sequence + host-vs-container DSN
explanation is in `${CLAUDE_SKILL_DIR}/references/dev-bootstrap.md`.

---

## Telemetry posture & OpenAPI

Both are env-driven and rarely require code changes. Read these reference files when wiring the matching
parts of `index.ts` / the controller:

- **Telemetry (env-driven OTLP/HTTP traces+logs via `@labspangaea/ts-lib/telemetry`):** `${CLAUDE_SKILL_DIR}/references/telemetry.md`
- **OpenAPI / Scalar UI (`@elysiajs/openapi`, validation rules, response envelope):** `${CLAUDE_SKILL_DIR}/references/openapi.md`

---

## Example

```bash
/create-elysia-app type=api name=order-service
```

```
order-service/
├── src/
│   ├── index.ts
│   ├── domain/order.ts
│   ├── port/{order.ts, order-service.ts}
│   ├── service/{order.ts, factory.ts, stub/order.ts}
│   ├── apperr/order.ts
│   ├── db/schema/order.ts
│   ├── adapter/inbound/http/{order.ts, order.dto.ts, health.ts}
│   ├── adapter/outbound/repository/order.ts
│   └── cmd/seed.ts
├── config/config.ts
├── drizzle.config.ts
├── package.json
├── tsconfig.json
├── Dockerfile
├── docker-compose.yml
└── .env
```
