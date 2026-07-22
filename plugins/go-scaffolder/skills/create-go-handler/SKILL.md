---
name: create-go-handler
description: Generate the HTTP handler (inbound adapter) for ONE entity in an existing Go service — emits framework-agnostic huma handler funcs + `RegisterRoutes` wiring across nethttp/gin/chi/mux/echo, with cursor + offset pagination, request validation, and humares envelopes. Has Mode A (new schema → also generates upstream domain/port/repo/service automatically) and Mode B (existing service → just the handler file). **Use this skill whenever the user wants to expose an entity over HTTP in an existing project — phrasings like 'add REST endpoints for X', 'create the handler for Y', 'wire up HTTP routes for entity Z', 'expose Subscription over HTTP', 'add CRUD endpoints for the new Customer entity', 'add inbound HTTP handling for X'.** Do NOT use to scaffold a fresh project (use `create-go-app`), data-layer only (use `create-go-repository`), or service-layer only (use `create-go-service`).
allowed-tools: [bash, read, write, edit, grep, glob, mcp__go-lsp__go_diagnose, AskUserQuestion]
model: sonnet
---

# Skill: create-go-handler

Generate the HTTP handler (inbound adapter) for one entity in a Go service, wired to its service layer. Use this skill whenever someone wants to add REST endpoints, an HTTP handler file, or route registration to an existing Go project. Trigger even if the user says "add endpoints for X", "create the handler for Y", or "wire up HTTP routes for entity Z".

## Parameters

| Parameter | Required | Default | Values |
|-----------|----------|---------|--------|
| `http_framework` | no | `gin` | `nethttp` · `gin` · `chi` · `mux` · `echo` |

## Prerequisites

| Item | Action if missing |
|------|-------------------|
| `go.mod` in working directory | Tell user this skill works inside an existing Go project |
| `internal/service/{entity}.go` | Mode A generates it inline; Mode B requires it to exist |

---

## Step 1 — Choose mode

Ask via `AskUserQuestion` so the user sees a structured choice:

```
AskUserQuestion({
  question: "How should we source the entity for this handler?",
  header:   "Mode",
  options: [
    { label: "New schema (Recommended)", description: "No service exists yet — generate the full stack (repo → service → handler)" },
    { label: "Existing service",         description: "Service layer already exists in internal/service/ — just generate the handler file" }
  ]
})
```

**Mode A — New schema**: User provides schema and framework. Claude generates repository layer, then service, then handler — all in sequence.

**Mode B — Existing service**: Run:

```bash
find internal/service -name "*.go" -not -name "*_test.go" 2>/dev/null
```

Surface the file pick:

- **≤4 results** — wrap the pick in a second `AskUserQuestion`, one option per filename.
- **>4 results** — fall back to a numbered list with a plain text prompt (`AskUserQuestion` is capped at 4 options).

Derive entity name from the chosen filename (e.g. `order.go` → `Order`).

Before generating, verify `internal/service/{{.EntityLower}}.go` exists. If missing, tell the user to run `/create-go-service` first and stop.

---

## Step 2 — Collect inputs

Read `go.mod` for `{{.Module}}`. Derive `{{.Entity}}` and `{{.EntityLower}}` from the picked service file or schema.

If `http_framework` was not passed as a parameter, ask via `AskUserQuestion`:

```
AskUserQuestion({
  question: "Which HTTP framework should the handler target?",
  header:   "HTTP framework",
  options: [
    { label: "gin (Recommended)", description: "github.com/gin-gonic/gin — the team's most common choice" },
    { label: "nethttp",           description: "Standard library net/http, zero deps" },
    { label: "chi",               description: "github.com/go-chi/chi/v5" },
    { label: "echo",              description: "github.com/labstack/echo/v4" }
  ]
})
```

`mux` (`github.com/gorilla/mux`) is still a valid value — it's reachable via the auto-added "Other" entry that accepts free-text. Map the selected label to the `http_framework` parameter (`gin` / `nethttp` / `chi` / `echo` / `mux`).

**Mode A only — parse schema**: Read and follow the schema parsing rules in `${CLAUDE_SKILL_DIR}/../create-go-repository/SKILL.md` (Step 4 — Collect inputs, "Schema parsing (Mode A)" subsection) to build `{{.Fields}}`.

**Mode B — reconstruct fields**: Read `internal/domain/{{.EntityLower}}.go` and build `{{.Fields}}` from the struct definition (same type-mapping rules). These are needed for `CreateRequest` / `UpdateRequest` field generation.

---

## Step 3 — Mode A: Generate upstream layers first

Read and execute in order:

1. `${CLAUDE_SKILL_DIR}/../create-go-repository/SKILL.md` — Mode A (new schema): generates domain + port + repository + apperr
2. `${CLAUDE_SKILL_DIR}/../create-go-service/SKILL.md` — Mode B (existing repo): generates service

Run `mcp__go-lsp__go_diagnose` on each generated file. Run `go build ./...`. Fix all errors before continuing to handler generation.

---

## Step 4 — Generate handler files

Handler templates are framework-agnostic — huma derives the OpenAPI spec from
the input/output struct types, and the chosen framework only matters for the
adapter constructor in `cmd/{name}/main.go`. Render all three:

| Template | Output |
|---|---|
| `${CLAUDE_SKILL_DIR}/../create-go-app/references/httphandler.go.tmpl` | `internal/adapter/inbound/httphandler/{{.EntityLower}}.go` |
| `${CLAUDE_SKILL_DIR}/../create-go-app/references/httphandler_dto.go.tmpl` | `internal/adapter/inbound/httphandler/{{.EntityLower}}_dto.go` |

Substitute `{{.Entity}}`, `{{.EntityLower}}`, `{{.Module}}`, `{{.Fields}}`.

If `{{.EntityLower}}.go` or `{{.EntityLower}}_dto.go` already exists, ask the user before overwriting.

### Key patterns enforced by templates

| Concern | Rule |
|---------|------|
| Struct name | `type {{.Entity}} struct` — entity-scoped, no collision when multiple handlers share the package |
| Constructor | `func New{{.Entity}}(svc {{.Entity}}Service) *{{.Entity}}` — the handler defines a narrow local `{{.Entity}}Service` interface; both `*service.{{.Entity}}` and `*stub.{{.Entity}}` satisfy it structurally. The factory `service.New{{.Entity}}Service(cfg, repo)` returns `port.{{.Entity}}Service` which also satisfies the local interface (same method set). |
| Route registration | `RegisterRoutes(api huma.API)` — called from main with the framework-specific `huma.API` adapter |
| Handler signature | `func (h *{{.Entity}}) method(ctx context.Context, input *XxxInput) (*XxxOutput, error)` |
| Success response (single) | `return humares.Data(entity), nil` |
| Success response (list) | `return humares.List(entities, humares.WithCursor[...](&humares.CursorPagination{...})), nil` |
| Error dispatch | `return nil, err` — huma renders via the `huma.NewError` override in main; `apierr.CodeErr`/`CodeErrEnum` set the HTTP status via `huma.StatusError` |
| Request validation | huma native JSON Schema validation — fields without `,omitempty` are required; `maxLength:"N"` enforces length. No `Resolve()`, no `validate.go`, no `SkipValidateBody`. |
| Cursor params | `repo.NewCursorParams(input.Cursor, input.Limit, repo.Descending("created_at"), repo.Asc("id"))` |
| Offset params | `repo.NewOffsetParams(*input.Offset, input.Limit)` — gated by `input.Offset != nil` |
| List filters | `ListXxxsInput.ToFilters() []repo.Filter` (Filterable pattern) |
| DELETE response | `return nil, nil` with `DefaultStatus: 204` on the operation |
| POST response | `DefaultStatus: 201` on the operation |
| PUT response | 200 OK (huma default) with updated entity body |

---

## Step 5 — Verify

1. `mcp__go-lsp__go_diagnose` on each generated `.go` file. Fix all errors.
2. `go build ./...` from project root. Fix all errors.
3. Do not report done until both pass clean.
