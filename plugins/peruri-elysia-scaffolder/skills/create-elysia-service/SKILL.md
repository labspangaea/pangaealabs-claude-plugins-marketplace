---
name: create-elysia-service
description: Generate the service (use-case) layer for ONE entity in an Elysia/Bun project wired to @peruri/ts-lib — the real service, the canned stub, the service-port interface, and the build-time stub factory. **Use this whenever someone wants to add a service file to an existing Bun project, implement business logic for an entity, or wire a service to an already-created repository** — phrasings like "create the service for X", "add business logic for Y", "wire up the use-case layer". Do NOT use to scaffold a fresh project (use `/peruri-elysia-scaffolder:create-elysia-app`), to generate the data layer only (use `create-elysia-repository`), or to expose endpoints (use `create-elysia-handler`).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__ts-lsp__ts_diagnose, AskUserQuestion]
model: inherit
---

# Skill: create-elysia-service

Generate `service` + `stub` + `service-port` + `factory` for one entity.

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `package.json` in cwd | Tell the user this works inside an existing Bun project |
| `src/port/{entityLower}.ts` with `{Entity}Repository` | Mode A generates it; Mode B requires it |

## Step 1 — Choose mode

```
AskUserQuestion({
  question: "How should we source the entity for this service?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "No repo exists yet — generate the full repository layer first via create-elysia-repository, then the service" },
    { label: "Existing repo",            description: "Repository already exists in src/adapter/outbound/repository/ — just generate the service files" }
  ]
})
```

**Mode A — New schema**: run `/create-elysia-repository` Mode A in full first (domain + port + repository + schema + apperr), `ts_diagnose` + `tsc` clean, then continue.

**Mode B — Existing repo**: `find src/adapter/outbound/repository -name '*.ts' -not -name '*.test.ts'`, surface the pick (≤4 → `AskUserQuestion`; >4 → numbered prompt). Derive `Entity` from the filename. Verify `src/port/{entityLower}.ts` has `{Entity}Repository` — if missing, tell the user to run `/create-elysia-repository` first and stop.

## Step 2 — Collect inputs

Read `package.json` `name` for `Module`. Derive `Entity`/`EntityLower`. Mode A: parse the schema per `/create-elysia-repository` Step 3.

## Step 3 — Render

Templates at `${CLAUDE_SKILL_DIR}/../create-elysia-app/references/`:

| Template | Output |
|---|---|
| `port_service.ts.tmpl` | `src/port/{entityLower}-service.ts` |
| `service.ts.tmpl` | `src/service/{entityLower}.ts` |
| `service_stub.ts.tmpl` | `src/service/stub/{entityLower}.ts` |
| `service_factory.ts.tmpl` | `src/service/factory.ts` (per-project) |

If `factory.ts` already exists (multiple entities), **add** the new entity's `new{Entity}Service` export to it rather than overwriting. If a per-entity file exists, ask before overwriting.

### Key patterns enforced by the templates
- The service holds `repo: port.{Entity}Repository` — depends on the port, never the concrete adapter (DIP); `implements {Entity}Service`.
- `create` generates a UUID + stamps timestamps; `update` is find-then-write (preserves `createdAt`, refreshes `updatedAt`).
- The stub (`src/service/stub/`) is stateless with deterministic ids `"{entityLower}-stub-<i>"` so FE fixtures survive restarts.
- The factory selects real vs stub: gated by the `SERVICE_STUB` compile-time constant (tree-shaken from the production `bun build`) and the runtime `SERVICE_BACKEND` env. See `/create-elysia-app` "Stub mode".

## Step 4 — Verify
1. `mcp__ts-lsp__ts_diagnose` on each generated file. Fix all errors.
2. `bunx tsc --noEmit` from the project root. Fix all errors.
3. `bun build ./src/index.ts --define SERVICE_STUB=true --outdir /tmp/stub-check` must also succeed (stub build links cleanly). Clean up `/tmp/stub-check` after.
4. Do not report done until all pass clean.
