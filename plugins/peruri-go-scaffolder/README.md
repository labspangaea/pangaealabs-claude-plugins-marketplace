# peruri-go-scaffolder

Scaffold production-ready Go services wired to `go-peruri-lib` (the team's hexagonal-architecture library). Generates domain types, ports, GORM repositories with optional caching, services, and HTTP handlers across 5 frameworks — or message-broker consumers/publishers across 3 brokers.

## Skills

| Skill | Use when you want to… |
|---|---|
| `/peruri-go-scaffolder:create-go-app` | Scaffold a complete service from scratch (orchestrates the 3 layered skills below, then adds `cmd/`, `config/`, `go.mod`). |
| `/peruri-go-scaffolder:create-go-repository` | Add a new entity's data layer (domain + port + GORM repository + apperr) to an existing project. |
| `/peruri-go-scaffolder:create-go-service` | Add the use-case/service layer for an existing port. |
| `/peruri-go-scaffolder:create-go-handler` | Add HTTP handler endpoints for an existing service (or generate the upstream layers in Mode A). |

## Parameters supported

- `type`: `api` · `consumer` · `publisher`
- `http_framework`: `nethttp` · `gin` · `chi` · `mux` · `echo`
- `broker`: `kafka` · `rabbitmq` · `redis`
- `database`: `gorm-postgres` · `gorm-mysql` · `none`
- `cache`: `none` · `redis` · `memory` · `couchbase`

The orchestrator collects missing parameters via sequential Q&A.

## Prerequisites

- **Go 1.26+** on `PATH`.
- **`go-peruri-lib`** accessible at the configured module prefix (`sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib`). By default (`libMode=git`) the generated `go.mod` has **no** `replace` directive — `go mod tidy` fetches the lib over `GOPRIVATE`. Set `libMode=local` in the config store to wire a local checkout via a `replace` directive instead (see [Configuration](#configuration)).
- **GitLab personal access token** for cloning `go-peruri-lib`. Stored at `~/.claude/secrets/peruri-gitlab.env` (mode `600`). The orchestrator prompts for it on first run if missing. Token needs at least `read_repository` scope.
- **`mcp__go-lsp__go_diagnose`** MCP tool registered in `~/.claude.json` (the skill calls it after every file write to catch type errors before reporting done). The Node wrapper for `go-lsp` lives in [`mcp-servers/go-lsp/`](../../mcp-servers/go-lsp/) in this repo — see [`mcp-servers/README.md`](../../mcp-servers/README.md) for one-time clone + `npm ci` + `~/.claude.json` snippet. Also requires `gopls` on `PATH` (`go install golang.org/x/tools/gopls@latest`).

## Configuration

The `go-peruri-lib` coordinates and import mode are configurable via a user-level
**config store** — `~/.peruri-go-scaffolder/config.json` — layered over the in-repo
defaults in `tools/config.env`. Precedence: **env var → `~/.peruri-go-scaffolder/config.json` → `tools/config.env` default**. Full schema: [`skills/create-go-app/references/config-store.md`](./skills/create-go-app/references/config-store.md).

| `config.json` key | Env var | Purpose | Default |
|---|---|---|---|
| `libLocalPath` | `PERURI_GO_LIB_PATH` | Local filesystem path of the cloned repo | `$HOME/go/src/sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib` |
| `remoteHost` | `PERURI_REMOTE_HOST` | GitLab host for the clone URL + GOPRIVATE host | `sipgn-git.bgn.go.id` |
| `remoteProject` | `PERURI_REMOTE_PROJECT` | GitLab project path (`namespace/repo`, no `.git`) | `harry.sitohang/go-peruri-lib` |
| `libMode` | `PERURI_GO_LIB_MODE` | `git` (fetch via GOPRIVATE, no replace) or `local` (add a `replace` to the local checkout) | `git` |

The sync script and the smoke runner read these at runtime (both source `config.env`).
To override per-shell, export the env var; to set a machine-wide default, write
`~/.peruri-go-scaffolder/config.json`; to change the project baseline, edit `tools/config.env`.

**Import mode** is the Go analog of the TS plugin's `file:`-vs-git-URL choice: `git`
keeps the original remote-fetch behavior; `local` redirects the generated `go.mod` to a
local checkout (`go mod edit -replace "$PERURI_GO_MODULE=$PERURI_GO_LIB_PATH"`). The
**module import path itself stays fixed** — `remoteHost` changes where the lib is fetched
from, not the import path written into source (that's the `sed` rehome below).

The Dockerfile's GOPRIVATE host is overridable at build time:
`docker build --build-arg GOPRIVATE_HOST=<host> .` (defaults to `remoteHost`).

**If the package URL ever moves**, `config.env` covers the orchestration layer (sync script, smoke runner). The 21 `.tmpl` files under `skills/create-go-app/references/` and the API reference at `references/codebase.md` embed the literal module path because they render directly into the user's Go source — for those, run a single `sed` pass:

```bash
PLUGIN=~/projects/claude-plugins/plugins/peruri-go-scaffolder
OLD="sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib"
NEW="new.host/path/go-peruri-lib"
grep -rl "$OLD" "$PLUGIN" --include='*.tmpl' --include='*.md' \
  | xargs sed -i '' "s|$OLD|$NEW|g"
```

Then update the four variables in `tools/config.env` to match.

## Auto-sync of `go-peruri-lib`

When `/peruri-go-scaffolder:create-go-app` starts, it runs `tools/sync-go-peruri-lib.sh` to ensure the local clone exists and is current. Behaviour:

1. **Missing clone** → clones from the GitLab URL (HTTPS with the token from `~/.claude/secrets/peruri-gitlab.env`).
2. **Existing clone** → detects the default branch (`main` preferred, else `master`), creates a temp git worktree at the branch tip, fetches `origin`, compares old vs new SHA.
3. **Updates available** → shows you the commit list and asks before fast-forwarding. Skipping is fine.

Your existing checkout is never touched. If your `go-peruri-lib` is on `main`/`master` with uncommitted changes, the script refuses to update that branch and tells you to commit/stash first. The final scaffolding summary records which `go-peruri-lib` SHA the project is wired against.

## Runtime tests

The `tools/smoke/` runner is **compile-only** — it proves the templates compile against `go-peruri-lib`. For runtime verification of generated services against real services, use `/peruri-go-scaffolder:integration-test-go-app`.

That skill brings up the bundled docker-compose stack (postgres + mysql + redis), renders representative API combos (5 by default), starts each generated binary, and runs a CRUD + cursor pagination + offset pagination + cache + structured-log assertion sequence against each. Reports pass/fail per combo; logs land at `skills/integration-test-go-app/logs/<combo>.log` for inspection.

Both pagination strategies are tested: cursor (default) and `?offset=N&limit=M`. The handler templates dispatch on the query param.

Prerequisites for the runtime test: `docker`, `jq`, `curl`, `go` on PATH, and `go-peruri-lib` at a commit that has `OffsetParamsFromRequest` (added in commit `3067123`).

## Install

### From git (teammates)

```
/plugin marketplace add <git-url>
/plugin install peruri-go-scaffolder@peruri-claude-plugins-marketplace
```

### From local path (dev)

```
/plugin marketplace add ~/projects/claude-plugins
/plugin install peruri-go-scaffolder@peruri-claude-plugins-marketplace
```

## Usage

```
/peruri-go-scaffolder:create-go-app type=api name=order-service
```

The skill will ask any unspecified parameters one at a time, then ask for the entity schema (accepted formats: JSON example, SQL `CREATE TABLE`, OpenAPI properties block, Postman example), then generate the project as a sibling directory to `go-peruri-lib`.

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
peruri-go-scaffolder/
├── .claude-plugin/plugin.json
├── README.md                        # this file
├── references/
│   └── codebase.md                  # 22 KB go-peruri-lib API reference (interfaces, types, patterns)
├── skills/
│   ├── create-go-app/
│   │   ├── SKILL.md                 # orchestrator — owns the templates
│   │   └── references/
│   │       ├── *.tmpl               # 23 Go text/template files
│   │       ├── preflight.md         # sync + GOPRIVATE gate + import-mode steps
│   │       └── config-store.md      # ~/.peruri-go-scaffolder/config.json schema
│   ├── create-go-handler/SKILL.md   # references templates via ${CLAUDE_SKILL_DIR}/../create-go-app/references/
│   ├── create-go-repository/SKILL.md
│   └── create-go-service/SKILL.md
└── tools/
    ├── config.env                   # in-repo defaults; layers ~/.peruri-go-scaffolder/config.json on top
    ├── sync-go-peruri-lib.sh        # clones/updates the lib reference checkout (reads config.env)
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
