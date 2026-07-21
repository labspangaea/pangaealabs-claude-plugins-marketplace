---
name: create-go-service
description: Generate the service (use-case) layer for one entity in a Go service, wired to its port interface. **Use this skill whenever someone wants to add a service file to an existing Go project wired to go-peruri-lib, implement business logic for an entity, or wire a service to an already-created repository** — phrasings like "create the service for X", "add business logic for Y entity", "wire up the use-case layer", "build the service layer for the Order entity". Do NOT use to scaffold a fresh Go project (use `/peruri-go-scaffolder:create-go-app`), to generate the data layer only (use `/peruri-go-scaffolder:create-go-repository`), or to expose endpoints over HTTP (use `/peruri-go-scaffolder:create-go-handler` — its Mode A generates the upstream service automatically).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__go-lsp__go_diagnose, AskUserQuestion]
model: sonnet
---

# Skill: create-go-service

Generate the service (use-case) layer for one entity in a Go service, wired to its port interface. Use this skill whenever someone wants to add a service file to an existing Go project, implement business logic for an entity, or wire a service to an already-created repository. Trigger even if the user says "create the service for X" or "add business logic for Y entity".

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `go.mod` in working directory | Tell user this skill works inside an existing Go project |
| `internal/port/{{.EntityLower}}.go` with `{{.Entity}}Repository` interface | Mode A generates it inline; Mode B requires it to exist |

---

## Step 1 — Choose mode

Ask via `AskUserQuestion` so the user sees a structured choice:

```
AskUserQuestion({
  question: "How should we source the entity for this service?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "No repo exists yet — generate the full repository layer first via /create-go-repository, then the service" },
    { label: "Existing repo",            description: "Repository layer already exists in internal/adapter/outbound/repository/ — just generate the service file" }
  ]
})
```

**Mode A — New schema**: User provides the entity schema. Claude generates the full repository layer first (domain + port + repository + apperr), then generates the service.

**Mode B — Existing repo**: Run:

```bash
find internal/adapter/outbound/repository -name "*.go" -not -name "*_test.go" 2>/dev/null
```

Surface the file pick using the same shape as Step 1:

- **≤4 results** — wrap the pick in a second `AskUserQuestion`, one option per filename.
- **>4 results** — fall back to a numbered list with a plain text prompt. `AskUserQuestion` only carries 4 options, so once a service has more entities than that the structured UI becomes lossy.

Derive entity name from the chosen filename (e.g. `order.go` → `Order`).

Before generating, verify `internal/port/{{.EntityLower}}.go` contains `type {{.Entity}}Repository interface`. If missing, tell the user to run `/create-go-repository` first and stop.

---

## Step 2 — Collect inputs

Read `go.mod` for `{{.Module}}`. Derive `{{.Entity}}` and `{{.EntityLower}}` from the picked repository file or schema.

**Mode A only — parse schema**: Read and follow the schema parsing rules in `${CLAUDE_SKILL_DIR}/../create-go-repository/SKILL.md` (Step 4 — Collect inputs, "Schema parsing (Mode A)" subsection) to build `{{.Fields}}`.

---

## Step 3 — Mode A: Generate repository layer first

Read `${CLAUDE_SKILL_DIR}/../create-go-repository/SKILL.md` and execute **Mode A (new schema)** in full:
- `internal/domain/{{.EntityLower}}.go`
- `internal/port/{{.EntityLower}}.go`
- `internal/adapter/outbound/repository/{{.EntityLower}}.go`
- `internal/apperr/{{.EntityLower}}.go`

Run `mcp__go-lsp__go_diagnose` on each file and run `go build ./...`. Fix all errors before continuing to the service step.

---

## Step 4 — Generate service-port interface

Template: `${CLAUDE_SKILL_DIR}/../create-go-app/references/port_service.go.tmpl`
Output: `internal/port/{{.EntityLower}}_service.go`

This file defines `port.{{.Entity}}Service` — the use-case contract the HTTP
handler depends on. Both the real service and the stub implement it.

If the file already exists, ask the user before overwriting.

---

## Step 5 — Generate service file

Template: `${CLAUDE_SKILL_DIR}/../create-go-app/references/service.go.tmpl`
Output: `internal/service/{{.EntityLower}}.go`

Substitute `{{.Entity}}`, `{{.EntityLower}}`, `{{.Module}}`, `{{.Fields}}`.

If the file already exists, ask the user before overwriting.

### Key patterns enforced by the template

- Service struct holds `repo port.{Entity}Repository` — depends on the port interface, never on the concrete adapter (DIP)
- Constructor: `New(repo port.{Entity}Repository) *{Entity}`
- Logger: `l := logger.FromContext(ctx)` inside each method — never injected as struct field
- Error wrapping: `fmt.Errorf("service: find {entityLower} %s: %w", id, err)` — adds context, doesn't swallow
- Methods: `Find`, `Create`, `Update`, `Delete`, `List`, `ListOffset`, `ListIDs` — each delegates directly to `s.repo.{Verb}{Entity}`
- `ListIDs` is generated as a thin delegation to `port.{Entity}Reader.List{Entity}IDs` — exposes lightweight ID-only reads for batch and event-driven use cases
- Compile-time assertion: `var _ port.{Entity}Service = (*{Entity})(nil)` — fails the build if a method drifts off the port

---

## Step 6 — Generate stub service file

Template: `${CLAUDE_SKILL_DIR}/../create-go-app/references/service_stub.go.tmpl`
Output: `internal/service/stub/{{.EntityLower}}.go`

The stub returns canned, shape-correct responses so the frontend can integrate
against the huma OpenAPI contract while the real service is still in progress.
The file starts with `//go:build stub` so production builds (no `-tags=stub`)
exclude it.

If the file already exists, ask the user before overwriting.

---

## Step 7 — Generate (or verify) factory files

Per-project, not per-entity. If `internal/service/factory_default.go` and
`internal/service/factory_stub.go` already exist, **add** the new entity's
factory function to each (alongside the existing entities' factories). If
they're missing, render both templates fresh:

| Template | Output |
|---|---|
| `${CLAUDE_SKILL_DIR}/../create-go-app/references/service_factory_default.go.tmpl` | `internal/service/factory_default.go` |
| `${CLAUDE_SKILL_DIR}/../create-go-app/references/service_factory_stub.go.tmpl` | `internal/service/factory_stub.go` |

The factories accept `(cfg config.Config, repo port.{Entity}Repository)` and
return `port.{Entity}Service`. Under the default build the factory returns
the real service unconditionally; under `-tags=stub` it switches on
`cfg.ServiceBackend`. See create-go-app/SKILL.md "Wiring Rules" for the rules
enforced.

---

## Step 8 — Verify

1. `mcp__go-lsp__go_diagnose` on `internal/service/{{.EntityLower}}.go`, `internal/service/stub/{{.EntityLower}}.go`, both factory files, and `internal/port/{{.EntityLower}}_service.go`. Fix all errors.
2. `go build ./...` from project root. Fix all errors.
3. `go build -tags=stub ./...` — must also pass clean.
4. Do not report done until all three pass clean.
