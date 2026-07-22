# go-scaffolder

Scaffold production-ready Go services wired to `go-lib` (the team's hexagonal-architecture library). Generates domain types, ports, GORM repositories with optional caching, services, and HTTP handlers across 5 frameworks — or message-broker consumers/publishers across 3 brokers.

## Skills

| Skill | Use when you want to… |
|---|---|
| `/go-scaffolder:create-go-app` | Scaffold a complete service from scratch (orchestrates the 3 layered skills below, then adds `cmd/`, `config/`, `go.mod`). |
| `/go-scaffolder:create-go-repository` | Add a new entity's data layer (domain + port + GORM repository + apperr) to an existing project. |
| `/go-scaffolder:create-go-service` | Add the use-case/service layer for an existing port. |
| `/go-scaffolder:create-go-handler` | Add HTTP handler endpoints for an existing service (or generate the upstream layers in Mode A). |

## Parameters supported

- `type`: `api` · `consumer` · `publisher`
- `http_framework`: `nethttp` · `gin` · `chi` · `mux` · `echo`
- `broker`: `kafka` · `rabbitmq` · `redis`
- `database`: `gorm-postgres` · `gorm-mysql` · `none`
- `cache`: `none` · `redis` · `memory` · `couchbase`

The orchestrator collects missing parameters via sequential Q&A.

## Prerequisites

- **Go 1.26+** on `PATH`, with network access to the public Go module proxy (`go env GOPROXY` — the default is fine).
- **`go-lib`** is a **public** Go module (`github.com/labspangaea/go-lib`). Generated services import `github.com/labspangaea/go-lib/...` and `go mod tidy` fetches it from the public proxy like any other dependency — **no token, no `GOPRIVATE`, no `replace` directive, no sync step.**
- **`mcp__go-lsp__go_diagnose`** MCP tool registered in `~/.claude.json` (the skill calls it after every file write to catch type errors before reporting done). The Node wrapper for `go-lsp` lives in [`mcp-servers/go-lsp/`](../../mcp-servers/go-lsp/) in this repo — see [`mcp-servers/README.md`](../../mcp-servers/README.md) for one-time clone + `npm ci` + `~/.claude.json` snippet. Also requires `gopls` on `PATH` (`go install golang.org/x/tools/gopls@latest`).

## Runtime tests

The `tools/smoke/` runner is **compile-only** — it proves the templates compile against `go-lib`. For runtime verification of generated services against real services, use `/go-scaffolder:integration-test-go-app`.

That skill brings up the bundled docker-compose stack (postgres + mysql + redis), renders representative API combos (5 by default), starts each generated binary, and runs a CRUD + cursor pagination + offset pagination + cache + structured-log assertion sequence against each. Reports pass/fail per combo; logs land at `skills/integration-test-go-app/logs/<combo>.log` for inspection.

Both pagination strategies are tested: cursor (default) and `?offset=N&limit=M`. The handler templates dispatch on the query param.

Prerequisites for the runtime test: `docker`, `jq`, `curl`, `go` on PATH. The driver's `go mod tidy` pulls `go-lib` from the public proxy.

## Install

### From git (teammates)

```
/plugin marketplace add <git-url>
/plugin install go-scaffolder@labspangaea-claude-plugins-marketplace
```

### From local path (dev)

```
/plugin marketplace add ~/projects/claude-plugins
/plugin install go-scaffolder@labspangaea-claude-plugins-marketplace
```

## Usage

```
/go-scaffolder:create-go-app type=api name=order-service
```

The skill will ask any unspecified parameters one at a time, then ask for the entity schema (accepted formats: JSON example, SQL `CREATE TABLE`, OpenAPI properties block, Postman example), then generate the project as a sibling directory to `go-lib`.

## Optional: enable the `go build` post-edit hook in your projects

The skill itself runs `mcp__go-lsp__go_diagnose` after each file write. If you also want a project-level `go build ./...` to run on every `.go` Edit/Write (catches cross-package issues the LSP misses), add this to your project's `.claude/settings.json` (**not** auto-installed by this plugin — opt in per project):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "jq -r '.tool_input.file_path // empty' | { read -r FILE; if [[ \"$FILE\" == *.go ]]; then DIR=$(dirname \"$FILE\"); while [[ \"$DIR\" != \"/\" && ! -f \"$DIR/go.mod\" ]]; do DIR=$(dirname \"$DIR\"); done; if [[ -f \"$DIR/go.mod\" ]]; then ERRS=$(cd \"$DIR\" && go build ./... 2>&1); if [[ -n \"$ERRS\" ]]; then jq -n --arg e \"$ERRS\" '{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":(\"go build errors:\\n\"+$e)}}'; fi; fi; fi; }",
        "timeout": 60,
        "statusMessage": "go build ./..."
      }]
    }]
  }
}
```

You'll likely also want to allow `Bash(go build *)` and `Bash(go vet *)` in your project's `.claude/settings.local.json` to suppress permission prompts on every hook fire.

## What's bundled

```
go-scaffolder/
├── .claude-plugin/plugin.json
├── README.md                        # this file
├── references/
│   └── codebase.md                  # 22 KB go-lib API reference (interfaces, types, patterns)
├── skills/
│   ├── create-go-app/
│   │   ├── SKILL.md                 # orchestrator — owns the templates
│   │   └── references/
│   │       ├── *.tmpl               # 23 Go text/template files
│   │       └── preflight.md         # toolchain + network + go-lsp prerequisite check
│   ├── create-go-handler/SKILL.md   # references templates via ${CLAUDE_SKILL_DIR}/../create-go-app/references/
│   ├── create-go-repository/SKILL.md
│   └── create-go-service/SKILL.md
└── tools/
    ├── render-file/                 # Go text/template renderer (one file at a time)
    └── smoke/                       # maintainer smoke runner (re-renders affected combos on .tmpl edits)
        ├── main.go
        ├── combos.go                # 16 combos: framework × broker × db × cache
        └── render.go
```

`tools/smoke/` is for the plugin maintainer — it lives in the plugin so it's versioned alongside the templates, but it's never invoked by users of the plugin.

## Architecture the generated apps follow

Hexagonal (Ports & Adapters):

```
cmd/{name}/main.go                       composition root
config/config.go                          env-based config
internal/domain/{entity}.go              business types + errors
internal/port/                            interfaces declared by the domain
internal/service/{entity}.go             use-cases; imports port only
internal/adapter/inbound/
  httphandler/handler.go                  (api) HTTP handlers
  subscriber/handler.go                   (consumer) message handlers
internal/adapter/outbound/
  repository/{entity}.go                  DB implementation of port interface
  publisher/publisher.go                  (publisher) message publisher
```

See `references/codebase.md` for the full library API (interfaces, type mappings, cache backends, error patterns).
