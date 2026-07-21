---
name: create-go-repository
description: Generate domain struct, port interface, GORM repository adapter, and apperr error codes for one entity in an existing Go project wired to go-peruri-lib. **Use this skill whenever someone wants to add a new entity's data layer, create a repository for a domain model, generate a GORM model + port interface, or scaffold the persistence layer without generating the full application** — phrasings like "I need a repo for X", "create the domain and repository for Y", "add Z to the database layer", "scaffold the GORM model for Order". Owns the schema-parsing rules other skills delegate to. Do NOT use to scaffold a fresh Go project (use `/peruri-go-scaffolder:create-go-app`), to add the business-logic layer (use `/peruri-go-scaffolder:create-go-service`), or to expose endpoints over HTTP (use `/peruri-go-scaffolder:create-go-handler` — its Mode A generates the upstream repository automatically).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__go-lsp__go_diagnose, AskUserQuestion]
model: sonnet
---

# Skill: create-go-repository

Generate domain struct, port interface, GORM repository adapter, and apperr error codes for one entity. Use this skill whenever someone wants to add a new entity's data layer to an existing Go project, create a repository for a domain model, generate a GORM model and port interface, or scaffold the persistence layer without generating the full application. Trigger even if the user just says "I need a repo for X" or "create the domain and repository for Y".

## Parameters

| Parameter | Required | Default | Values |
|-----------|----------|---------|--------|
| `database` | no | `gorm-postgres` | `gorm-postgres` · `gorm-mysql` · `none` |
| `cache` | no | `none` | `none` · `redis` · `memory` · `couchbase` |

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `go.mod` in working directory | Tell user this skill works inside an existing Go project; suggest `/create-go-app` to start fresh |
| Entity schema OR existing domain file | **Ask** — see Mode selection below |
| Git module path prefix | `sipgn-git.bgn.go.id/harry.sitohang` (use as default if `go.mod` is absent) |

---

## Step 1 — Choose mode

Ask via `AskUserQuestion` so the user sees a structured choice rather than reading two flavor descriptions out of prose:

```
AskUserQuestion({
  question: "How should we source the entity for this repository?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "Paste JSON / SQL / OpenAPI / Postman — generate domain + port + repository + apperr from scratch" },
    { label: "Existing domain",          description: "Reuse an existing internal/domain/*.go file — generate only port + repository + apperr" }
  ]
})
```

**Mode A — New schema**: User provides the entity schema. Accepted formats:
- JSON example `{"name": "iPhone 15", "price": 999.99}`
- SQL `CREATE TABLE` script
- Swagger / OpenAPI `properties:` block
- Postman request body JSON

**Mode B — Existing domain**: Run:

```bash
find internal/domain -name "*.go" -not -name "*_test.go" 2>/dev/null
```

Then surface the file pick. `AskUserQuestion` is capped at 4 options, so the two branches are:

- **≤4 results** — wrap the pick in a second `AskUserQuestion`, one option per filename. This keeps the structured UX consistent with Step 1.
- **>4 results** — fall back to a numbered list and a plain text prompt. The capped-options ceiling means once a project grows past a handful of entities, plain text is the only honest UI.

Read the struct from the chosen file to extract fields. Skip domain generation (it already exists); generate only port + repository + apperr.

If `internal/` doesn't exist at all, suggest `/create-go-app` instead.

---

## Template Syntax

Templates use Go `text/template`. Some files (`repository.go.tmpl`, `config.go.tmpl`) contain `{{if eq .Cache "redis"}}…{{end}}` blocks that gate sections by the user's `cache` parameter. Evaluate conditionals against the chosen parameters — same way you handle `{{.Entity}}` substitution.

---

## Step 2 — Database choice

If `database` was not supplied as a parameter, ask:

```
AskUserQuestion({
  question: "Which database backend should the repository target?",
  header:   "Database",
  options: [
    { label: "PostgreSQL via GORM (Recommended)", description: "gorm-postgres — default for new repositories" },
    { label: "MySQL via GORM",                    description: "gorm-mysql" },
    { label: "None",                              description: "No persistence — generate domain + port only, skip the GORM adapter" }
  ]
})
```

Map the selected label to the `database` parameter (`gorm-postgres` / `gorm-mysql` / `none`). When the user picks `None`, skip Step 3 entirely — there is no repository to cache.

## Step 3 — Cache wrapper choice

Skip this question when `database == none` (nothing to cache).

If `cache` was not supplied as a parameter, ask:

```
AskUserQuestion({
  question: "Should this repository have a cache wrapper?",
  header:   "Cache",
  options: [
    { label: "None (Recommended)", description: "Direct SQL only — single New(db) constructor" },
    { label: "Redis",              description: "Generates both New(db) and NewCached(db, c, opts...) — Redis backend" },
    { label: "In-memory",          description: "Same two constructors — in-process cache (single-pod only)" },
    { label: "Couchbase",          description: "Same two constructors — Couchbase backend" }
  ]
})
```

Map the selected label to the `cache` parameter (`none` · `redis` · `memory` · `couchbase`). The library's `repo.CachedRepo` (in `db/repo/cached.go`) handles all caching logic — this skill only emits the wiring. Collapsing the old two-step ask ("cache yes/no, then which backend?") into one 4-option question keeps the dialog short and matches the shape of `/create-go-app` Step 6.

---

## Step 4 — Collect inputs

### Module path
Read `go.mod` (first line: `module <path>`). Use as `{{.Module}}`.

### Entity name
| Variable | Rule | Example |
|----------|------|---------|
| `{{.Entity}}` | PascalCase singular noun | `Product` |
| `{{.EntityLower}}` | lowercase | `product` |

- Mode A: derive from the schema (table name, JSON key prefix, or ask the user)
- Mode B: derive from the filename (`internal/domain/order.go` → `Order`)

### Schema parsing (Mode A)

Parse the schema into `{{.Fields}}`. Always strip system fields (`id`, `created_at`, `updated_at`) if present — they are injected automatically.

**Type mapping:**

| SQL / JSON / OAS type | Go type |
|-----------------------|---------|
| `VARCHAR`, `TEXT`, `CHAR`, string | `string` |
| `INT`, `BIGINT`, `INTEGER`, number (integer) | `int64` |
| `FLOAT`, `DOUBLE`, `DECIMAL`, number (float) | `float64` |
| `BOOLEAN`, `BOOL`, `TINYINT(1)`, boolean | `bool` |
| `TIMESTAMP`, `DATETIME`, string (date-time) | `time.Time` |
| `UUID` | `string` |

**Nullable fields**: column allows `NULL` / `nullable: true` / absent from `required` → prepend `*` (e.g. `string` → `*string`).

**`validate` tag:**

| Condition | Tag |
|-----------|-----|
| NOT NULL / in `required` array | `required` |
| `VARCHAR(n)` / `maxLength: n` | `required,max=N` |
| nullable / optional | `` (omit tag entirely) |

**FieldDef attributes** (used in templates via `{{range .Fields}}`):

| Attribute | Description | Example |
|-----------|-------------|---------|
| `.Name` | PascalCase Go identifier | `PetID`, `ShipDate` |
| `.GoType` | Go type string | `string`, `*int64`, `bool`, `time.Time` |
| `.JSONName` | snake_case json tag | `pet_id`, `ship_date` |
| `.DBColumn` | snake_case gorm column | `pet_id`, `ship_date` |
| `.Validate` | validate tag content | `required`, `required,max=255`, `` |

### Extract fields from existing domain (Mode B)

Read the Go struct and build `{{.Fields}}` using the type table above. Ignore `ID`, `CreatedAt`, `UpdatedAt`.

---

## Step 5 — System fields (always injected)

| Field | Domain type | GORM model type | GORM tag |
|-------|-------------|-----------------|----------|
| `ID` | `string` | `string` | `gorm:"primaryKey;column:id"` |
| `CreatedAt` | `time.Time` | `int64` | `gorm:"column:created_at;autoCreateTime:milli"` |
| `UpdatedAt` | `time.Time` | `int64` | `gorm:"column:updated_at;autoUpdateTime:milli"` |

---

## Step 6 — Generate files

Templates live at `${CLAUDE_SKILL_DIR}/../create-go-app/references/`. Substitute `{{.Entity}}`, `{{.EntityLower}}`, `{{.Module}}`, `{{.Fields}}` into each.

**Mode A — generate all 4:**

| Template | Output path |
|----------|-------------|
| `domain.go.tmpl` | `internal/domain/{{.EntityLower}}.go` |
| `port.go.tmpl` | `internal/port/{{.EntityLower}}.go` |
| `repository.go.tmpl` | `internal/adapter/outbound/repository/{{.EntityLower}}.go` |
| `apperr.go.tmpl` | `internal/apperr/{{.EntityLower}}.go` |

**Mode B — generate 3 (domain already exists):**

| Template | Output path |
|----------|-------------|
| `port.go.tmpl` | `internal/port/{{.EntityLower}}.go` |
| `repository.go.tmpl` | `internal/adapter/outbound/repository/{{.EntityLower}}.go` |
| `apperr.go.tmpl` | `internal/apperr/{{.EntityLower}}.go` |

### Apperr base offset

Before generating `internal/apperr/{{.EntityLower}}.go`, scan existing `internal/apperr/*.go` files for lines matching `iota + N`. Set `{{.ApperrBase}}` = highest N found + 1000, defaulting to 1000 if no files exist. This prevents numeric collisions in `apierr.AppendCodeErrMap`.

If an output file already exists, ask the user before overwriting.

### Key patterns enforced by the templates

- `orderModel` implements `TableName()`, `PrimaryKey()`, `GetPK()`, `CursorValues()` (required by `repo.Model[ID]`)
- `CursorValues()` returns every column that may appear in `OrderBy`
- Repository embeds `repo.Repository[model, string]` (interface) — accepts either `*repo.BaseRepo` (via `New`) or `*repo.CachedRepo` (via `NewCached`)
- `mapEntityRepoErr` private helper centralises repo-sentinel → apperr mapping (replaces per-method switch)
- `repo.ErrNotFound` → `apperr.ErrXxxNotFound` (never `gorm.ErrRecordNotFound` directly)
- apperr constants start at `iota + 1000` to avoid collisions with library codes
- `Update{{Entity}}` passes an explicit `[]string` column list to `repo.Repository.Update` — only user-defined field columns and `"updated_at"` are listed, so `id` and `created_at` are never clobbered by an update call
- `List{{Entity}}IDs` is generated in both the port interface and the repository adapter — thin wrapper over the embedded `repo.Repository.ListIDs`, exposed so services can perform batch/fan-out operations without loading full entities

### Cache constructor — emit only when `cache != none`

`repository.go.tmpl` includes a `NewCached(db, c, opts...)` constructor and a `cache` package import. When `cache == none`:

- Strip the `NewCached` function block.
- Strip the `"sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib/cache"` import line.

When `cache != none`:

- Keep both `New` and `NewCached`. The user picks at the call site in `main.go`.
- The cache key prefix is hardcoded to `"{{.EntityLower}}"` inside `NewCached` — `CachedRepo` namespaces with `"<prefix>:<id>"`. **Do not** also pass `WithKeyPrefix` to the cache backend constructor; it would double-prefix.

---

## Step 7 — Print main.go wiring snippet

This skill writes only the entity files. It does **not** edit `cmd/{name}/main.go`. After generation, print the copy-pasteable wiring snippet for the user to paste into `main.go`.

For `cache=redis` / `cache=memory` / `cache=couchbase`, read the snippet that matches the chosen backend from `${CLAUDE_SKILL_DIR}/../create-go-app/references/cache-backends.md` and print it inline, substituting `{{.Entity}}` and `{{.EntityLower}}` for the active entity. That file is the single source of truth — the `main_api_*` templates render the same wiring, and `/peruri-go-scaffolder:create-go-app` Step 6 points to the same doc.

For `cache=none`, no snippet is needed — keep using `repository.New(gormDB)`.

The user must also ensure `Config` has the relevant fields (`CacheTTL`, `CacheJitterFactor`, plus per-backend connection fields). Tell them to mirror the `config.go.tmpl` cache section from `/create-go-app`.

---

## Step 8 — Verify

After writing every file:

1. Run `mcp__go-lsp__go_diagnose` on each generated `.go` file. Fix all errors.
2. Run `go build ./...` from the project root. Fix all errors.
3. Do not report done until both checks pass clean.

---

## Code style

| Rule | Do | Don't |
|------|----|-------|
| Imports | `stdlib` → blank → `external` → blank → `internal` | mixed groups |
| Error wrapping | `fmt.Errorf("repository: find %s: %w", id, err)` | bare `errors.New(...)` with context |
| Package names | `repository`, `domain`, `port` | `orderRepository`, `IPort` |
| Comments | exported symbols only | implementation-detail comments |
