# Preflight — Bun + network + ts-lsp gate

Two hard gates plus a network check gate the scaffold. Run all before collecting
inputs. `@labspangaea/ts-lib` is a **public** npm package — generated services
depend on it directly and `bun install` fetches it from the public registry. There
is no registry token, no `.npmrc` auth, no `file:` sibling path, and no config store.

## 1. Bun present (hard gate)

```bash
bun --version
```

If missing: tell the user to install Bun (`curl -fsSL https://bun.sh/install | bash`)
and re-invoke. The whole toolchain — runtime, bundler, package manager, test
runner — is Bun.

## 2. Network reachable for the public registry (best-effort)

`@labspangaea/ts-lib` is a **public** npm package. The generated `package.json`
depends on it directly (`"@labspangaea/ts-lib": "^0.1.0"`), and `bun install`
fetches it from the public npm registry like any other dependency. Nothing to
configure: no registry token, no `.npmrc`/bunfig auth, no `file:` sibling checkout,
no config store.

Best-effort connectivity check (do not hard-block — `bun install` will surface a
clear error if the registry is unreachable):

```bash
bun pm view @labspangaea/ts-lib version >/dev/null 2>&1 && echo registry-ok || echo "registry unreachable — check network"
```

## 3. `mcp__ts-lsp__ts_diagnose` available (hard gate)

The skill calls it after every generated `.ts` file to catch type errors before
reporting done (the analog of the Go plugin's `go_diagnose` gate). If the tool is
not registered, tell the user to add the `ts-lsp` MCP server to `~/.claude.json`
and ensure `typescript` is installed, then re-invoke. Without it the skill cannot
fail-closed on type errors.

## Notes
- Generated apps are standalone projects placed wherever the user names them;
  `bun install` pulls `@labspangaea/ts-lib` from the public registry — no sibling
  checkout or workspace layout is required.
- Bun auto-loads `.env`, so `bun run src/index.ts` picks up `DATABASE_DSN` etc.
  without a dotenv dependency.
