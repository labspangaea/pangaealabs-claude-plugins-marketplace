# Preflight — Bun + `@peruri/ts-lib` + ts-lsp gate

Three checks gate the scaffold. Run all before collecting inputs. The Bun and
ts-lsp checks are hard gates; the lib-resolution check is best-effort (falls back
to the workspace).

## 1. Bun present (hard gate)

```bash
bun --version
```

If missing: tell the user to install Bun (`curl -fsSL https://bun.sh/install | bash`)
and re-invoke. The whole toolchain — runtime, bundler, package manager, test
runner — is Bun.

## 2. `@peruri/ts-lib` resolvable (best-effort)

**First, resolve the configured source.** The repo URL and the `package.json`
dependency value are read from the config store — see
`${CLAUDE_SKILL_DIR}/references/config-store.md` for the full schema and precedence
(`env > ~/.peruri-elysia-scaffolder/config.json > default`). Run the resolver:

```bash
CFG="${HOME}/.peruri-elysia-scaffolder/config.json"
cfg() { [ -f "$CFG" ] && command -v jq >/dev/null 2>&1 && jq -r --arg k "$1" '.[$k] // empty' "$CFG" 2>/dev/null; }
TS_LIB_SOURCE="${PERURI_TS_LIB_SOURCE:-$(cfg tsLibSource)}";       TS_LIB_SOURCE="${TS_LIB_SOURCE:-https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib}"
TS_LIB_DEPENDENCY="${PERURI_TS_LIB_DEPENDENCY:-$(cfg tsLibDependency)}"; TS_LIB_DEPENDENCY="${TS_LIB_DEPENDENCY:-file:../peruri-ts-lib}"
echo "ts-lib source=$TS_LIB_SOURCE dependency=$TS_LIB_DEPENDENCY"
```

`TS_LIB_DEPENDENCY` becomes the `TsLibDependency` render param (written into the
generated `package.json`). Two supported source styles (the GOPRIVATE-vs-`replace`
analog of the Go plugin), selected by what `TS_LIB_DEPENDENCY` resolves to:

- **Bun workspace (default, `file:../peruri-ts-lib`)** — a sibling checkout of
  `peruri-ts-lib` exists. Check, and clone from the configured source if missing:
  ```bash
  test -d ../peruri-ts-lib && echo workspace-ok || git clone "$TS_LIB_SOURCE" ../peruri-ts-lib
  ```
- **GitLab private npm registry (`^0.1.0`, the GOPRIVATE analog)** — `~/.bunfig.toml` /
  `.npmrc` configures the `@peruri` scope with a registry URL + token:
  ```bash
  grep -q '@peruri' ~/.bunfig.toml ~/.npmrc 2>/dev/null && echo registry-ok
  ```

If neither resolves, prefer the workspace path: clone `peruri-ts-lib` from
`$TS_LIB_SOURCE` as a sibling and keep `file:../peruri-ts-lib`. Never block
scaffolding on a registry hiccup — the workspace fallback always works for local dev.
Set a non-default coordinate once via `~/.peruri-elysia-scaffolder/config.json`
rather than hand-editing the generated `package.json`.

## 3. `mcp__ts-lsp__ts_diagnose` available (hard gate)

The skill calls it after every generated `.ts` file to catch type errors before
reporting done (the analog of the Go plugin's `go_diagnose` gate). If the tool is
not registered, tell the user to add the `ts-lsp` MCP server to `~/.claude.json`
and ensure `typescript` is installed, then re-invoke. Without it the skill cannot
fail-closed on type errors.

## Notes
- Generated apps are placed as a **sibling to `peruri-ts-lib`** (mirroring the Go
  plugin's sibling-to-`go-peruri-lib` placement), so `file:../peruri-ts-lib`
  resolves and `bun install` links it.
- Bun auto-loads `.env`, so `bun run src/index.ts` picks up `DATABASE_DSN` etc.
  without a dotenv dependency.
