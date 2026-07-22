# Preflight — prerequisite check

This reference holds the single preflight check the `create-go-app` orchestrator runs **before** collecting any user inputs. The entry-point SKILL.md keeps a short checklist; the exact bash and remediation copy live here.

`go-lib` is a **public** Go module — `github.com/labspangaea/go-lib`. Generated services import `github.com/labspangaea/go-lib/...`, and `go mod tidy` fetches it from the public Go module proxy like any other dependency. **There is no token, no `GOPRIVATE`, no `replace` directive, and no sync step.** Preflight therefore only confirms the toolchain, network access, and the diagnostics MCP are present.

## Prerequisite gate

Confirm the local environment before collecting any other inputs:

```bash
# 1. Go toolchain 1.26+
go version

# 2. Network reachability to the public module proxy (go-lib is fetched from here)
go env GOPROXY   # expect the default: https://proxy.golang.org,direct
```

- **Go toolchain.** Require Go **1.26+** on `PATH`. If `go version` reports older or Go is missing, tell the user to install/upgrade Go and stop.
- **Network + proxy.** `go mod tidy` must be able to reach the public proxy (`proxy.golang.org` by default) to download `go-lib` and its transitive dependencies. If the user is offline or has `GOPROXY=off`, `go mod tidy` will fail in Post-Generation — flag it here so it's an actionable message, not a mysterious build error later.
- **`go-lsp` MCP for diagnostics.** The skill calls `mcp__go-lsp__go_diagnose` after every file write to catch type errors before reporting done. Confirm the tool is registered; if it is not, warn the user that generated files won't be type-checked and let them decide whether to continue.

There is nothing to authenticate and no local checkout to prepare — proceed to Step 1 once the toolchain and network are confirmed.
