---
name: create-elysia-repository
description: Generate the domain type, repository port, Drizzle repository adapter, Drizzle table schema, and apperr error codes for ONE entity in an existing Elysia/Bun project wired to @peruri/ts-lib. **Use this whenever someone wants to add a new entity's data layer, create a repository for a domain model, generate a Drizzle schema + port interface, or scaffold the persistence layer without generating the whole app** — phrasings like "I need a repo for X", "create the domain and repository for Y", "add Z to the database layer", "scaffold the Drizzle model for Order". Owns the schema-parsing rules the other layered skills delegate to. Do NOT use to scaffold a fresh project (use `/peruri-elysia-scaffolder:create-elysia-app`), to add the service layer (use `create-elysia-service`), or to expose endpoints (use `create-elysia-handler`).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__ts-lsp__ts_diagnose, AskUserQuestion]
model: inherit
---

# Skill: create-elysia-repository

Generate `domain` + `port` + Drizzle `repository` + Drizzle `schema` + `apperr` for one entity.

## Parameters

| Parameter | Required | Default | Values |
|-----------|----------|---------|--------|
| `database` | no | `drizzle-postgres` | `drizzle-postgres` · `drizzle-mysql` · `none` |
| `cache` | no | `none` | `none` · `redis` · `memory` · `couchbase` |

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `package.json` + `tsconfig.json` in cwd | Tell the user this skill works inside an existing Bun project; suggest `/create-elysia-app` to start fresh |
| `@peruri/ts-lib` resolvable | `bun install` first; the lib must be linked (workspace/registry) |
| Entity schema OR existing domain file | **Ask** — see Mode selection |

## Step 1 — Choose mode

```
AskUserQuestion({
  question: "How should we source the entity for this repository?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "Paste JSON / SQL / OpenAPI / Postman — generate domain + port + repository + schema + apperr from scratch" },
    { label: "Existing domain",          description: "Reuse an existing src/domain/*.ts file — generate only port + repository + schema + apperr" }
  ]
})
```

**Mode A — New schema**: user provides the entity schema (JSON example / SQL `CREATE TABLE` / OpenAPI `properties:` / Postman body).

**Mode B — Existing domain**: `find src/domain -name '*.ts' -not -name '*.test.ts'`, surface the pick (≤4 → `AskUserQuestion`, one option per file; >4 → numbered text prompt). Read the interface to extract fields; skip domain generation.

## Step 2 — Database & cache

Ask `database` then (if `database != none`) `cache` via `AskUserQuestion` (same option lists as `/create-elysia-app` Steps 3–4). Map labels → `drizzle-postgres`/`drizzle-mysql`/`none` and `none`/`redis`/`memory`/`couchbase`.

## Step 3 — Schema parsing (the canonical rules other skills delegate to)

Parse the schema into `Fields`. Always strip system fields (`id`, `created_at`/`createdAt`, `updated_at`/`updatedAt`) — they are injected.

**Type mapping** (SQL / JSON / OAS → TS domain · TypeBox · Drizzle column):

| Source | TS type | TypeBox | Drizzle |
|---|---|---|---|
| VARCHAR/TEXT/CHAR/string | `string` | `t.String()` | `varchar`/`text` |
| INT/INTEGER/number(int) | `number` | `t.Integer()` | `integer` |
| BIGINT | `number` | `t.Integer()` | `bigint({mode:'number'})` |
| FLOAT/DOUBLE/DECIMAL/number(float) | `number` | `t.Number()` | `doublePrecision` |
| BOOLEAN/BOOL/TINYINT(1) | `boolean` | `t.Boolean()` | `boolean` |
| TIMESTAMP/DATETIME/date-time | `Date` | `t.String({format:'date-time'})` | `bigint({mode:'number'})` |
| UUID | `string` | `t.String({format:'uuid'})` | `varchar` |

**Nullable** (NULL / `nullable:true` / not in `required`): TS type `T | null`; Drizzle drops `.notNull()`.

**FieldDef** (used by the templates): `.Name` (camelCase), `.GoType` (TS type string incl. `| null`), `.JSONName` (snake_case wire), `.DBColumn` (snake_case), `.Validate` (`required` / `required,max=N` / ``). The name `GoType` is kept so the Params shape matches the renderer's `FieldDef`.

**System fields** (always injected): `id` (`string`, varchar(36) PK), `createdAt`/`updatedAt` (`Date` domain, `bigint` epoch-ms column). The repository maps `bigint(string from driver) → Number → Date`.

## Step 4 — Apperr base offset

Before generating `src/apperr/{entityLower}.ts`, scan existing `src/apperr/*.ts` for `BASE = N`. Set `ApperrBase` = highest N + 1000, default 1000. Prevents code collisions.

## Step 5 — Render

Build the Params JSON (see `/create-elysia-app` "Template Rendering") and render via `bun ${CLAUDE_SKILL_DIR}/../../tools/render-file/index.ts`. Templates live at `${CLAUDE_SKILL_DIR}/../create-elysia-app/references/`.

| Mode | Templates → output |
|---|---|
| A | `domain.ts.tmpl` → `src/domain/{e}.ts`; `port.ts.tmpl` → `src/port/{e}.ts`; `apperr.ts.tmpl` → `src/apperr/{e}.ts`; `schema.ts.tmpl` → `src/db/schema/{e}.ts` (skip if `database=none`); `repository.ts.tmpl` → `src/adapter/outbound/repository/{e}.ts` (skip if `database=none`) |
| B | same as A minus `domain.ts.tmpl` |

If an output file exists, **ask before overwriting**.

### Key patterns enforced by the templates
- The repository implements the domain-typed `port.{Entity}Repository`, internally wrapping `repo.BaseRepo`/`CachedRepo` over a snake_case `{Entity}Row` + a `ModelMeta` (Drizzle 0.38 has no runtime reflection).
- `toDomain`/`toRow` map row↔domain; **Date fields coerce `new Date(Number(col))`** (Postgres bigint arrives as a string).
- `mapRepoErr` maps `repo.ErrNotFound` → `new ApiError(Err{Entity}NotFound)`.
- `update` passes an explicit column list (never clobbers `id`/`created_at`).
- `newCached{Entity}Repository` is emitted only when `cache != none`; the key prefix is owned by `makeCachedRepository` (no double-prefix on the backend).

## Step 6 — Verify
1. `mcp__ts-lsp__ts_diagnose` on each generated `.ts`. Fix all errors.
2. `bunx tsc --noEmit` from the project root. Fix all errors.
3. Do not report done until both pass clean.
