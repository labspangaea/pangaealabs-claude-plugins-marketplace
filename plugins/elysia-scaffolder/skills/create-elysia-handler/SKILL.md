---
name: create-elysia-handler
description: Generate the HTTP controller (inbound adapter) for ONE entity in an existing Elysia/Bun project — a thin idiomatic Elysia instance with TypeBox DTOs, cursor pagination, request validation, and the humares-style response envelopes, wired to the entity's service. Has Mode A (new schema → also generates the upstream domain/port/repo/service) and Mode B (existing service → just the controller + DTO). **Use this whenever the user wants to expose an entity over HTTP in an existing project — phrasings like 'add REST endpoints for X', 'create the handler/controller for Y', 'wire up HTTP routes for entity Z', 'expose Subscription over HTTP', 'add CRUD endpoints for the Customer entity'.** Do NOT use to scaffold a fresh project (use `create-elysia-app`), data-layer only (use `create-elysia-repository`), or service-layer only (use `create-elysia-service`).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__ts-lsp__ts_diagnose, AskUserQuestion]
model: inherit
---

# Skill: create-elysia-handler

Generate the Elysia controller + TypeBox DTO for one entity, wired to its service.

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `package.json` in cwd | Tell the user this works inside an existing Bun project |
| `src/service/{entityLower}.ts` | Mode A generates it; Mode B requires it |

## Step 1 — Choose mode

```
AskUserQuestion({
  question: "How should we source the entity for this controller?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "No service exists yet — generate the full stack (repo → service → controller)" },
    { label: "Existing service",         description: "Service already exists in src/service/ — just generate the controller + DTO" }
  ]
})
```

**Mode A — New schema**: run, in order, `/create-elysia-repository` (Mode A) then `/create-elysia-service` (Mode B), `tsc` clean, then generate the controller.

**Mode B — Existing service**: `find src/service -maxdepth 1 -name '*.ts' -not -name '*.test.ts'`, surface the pick. Derive `Entity` from the filename. Verify `src/service/{entityLower}.ts` exists; if missing, tell the user to run `/create-elysia-service` first and stop. Read `src/domain/{entityLower}.ts` to reconstruct `Fields` (for the DTO).

## Step 2 — Render

Templates at `${CLAUDE_SKILL_DIR}/../create-elysia-app/references/`:

| Template | Output |
|---|---|
| `dto.ts.tmpl` | `src/adapter/inbound/http/{entityLower}.dto.ts` |
| `controller.ts.tmpl` | `src/adapter/inbound/http/{entityLower}.ts` |

Then tell the user to mount it in `src/index.ts`: `.use({entityLower}Controller(svc))`. If the files exist, ask before overwriting.

### Key patterns enforced by the templates
| Concern | Rule |
|---|---|
| Controller | a thin `new Elysia({ prefix: '/api/v1/{entityLower}s' })` — serializes HTTP only, delegates to the service port |
| Routes | `list` (cursor) · `get` · `create` (201) · `update` · `delete` (204) |
| Validation | TypeBox `body` schema on POST/PUT — drives runtime validation AND the OpenAPI schema; failures become a 422 envelope via the server plugin's `onError` |
| Wire mapping | `bodyToInput` (snake_case body → camelCase domain) and `toResponse` (domain → snake_case wire, `Date` → ISO) keep the wire identical to the Go service |
| Cursor | `cursorParamsFromQuery(sp, 20, desc('created_at'), asc('id'))` |
| Errors | `throw new ApiError(...)`; the server plugin renders the envelope — never build error JSON by hand |
| Success | `data(...)` / `list(rows.map(toResponse), withCursor({...}))` |

## Step 3 — Verify
1. `mcp__ts-lsp__ts_diagnose` on each generated file. Fix all errors.
2. `bunx tsc --noEmit` from the project root. Fix all errors.
3. Do not report done until both pass clean.
