# Config store — `~/.peruri-elysia-scaffolder/config.json`

The `@peruri/ts-lib` **source** is configurable so a different checkout, fork, or
private-registry coordinate can be used without editing the plugin. The import
specifier stays `@peruri/ts-lib` everywhere (it is the package name baked into every
generated `import`); only **where that package comes from** is configurable — the
exact analog of the Go plugin's "host + clone source, module path fixed" rule.

## Location & shape

`~/.peruri-elysia-scaffolder/config.json` (optional — every key has a built-in default):

```json
{
  "tsLibSource": "https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib",
  "tsLibDependency": "file:../peruri-ts-lib"
}
```

| Key | Meaning | Default |
|-----|---------|---------|
| `tsLibSource` | Canonical repo URL — where to `git clone` the workspace sibling from, and what docs/preflight point at. | `https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib` |
| `tsLibDependency` | The literal value written into the generated `package.json` `dependencies["@peruri/ts-lib"]`. Workspace path, registry semver, or git spec. | `file:../peruri-ts-lib` |
| `tsLibLocalPath` *(optional, maintainer)* | Absolute path to a local `peruri-ts-lib` checkout for the `tools/smoke` compile matrix. Honored only by smoke, after `PERURI_TS_LIB`. | `~/projects/peruri-ts-lib` |

`tsLibDependency` examples:
- `file:../peruri-ts-lib` — Bun workspace sibling (default, best for local dev).
- `^0.1.0` — `@peruri` private npm registry (the GOPRIVATE analog; needs `~/.bunfig.toml`/`.npmrc`).
- `git+https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib.git#v0.1.0` — direct git dependency.

## Precedence (highest wins)

1. Environment variable — `PERURI_TS_LIB_SOURCE`, `PERURI_TS_LIB_DEPENDENCY`
2. `~/.peruri-elysia-scaffolder/config.json`
3. Built-in default (the values above)

## Resolver (run in preflight, before assembling PARAMS)

```bash
CFG="${HOME}/.peruri-elysia-scaffolder/config.json"
cfg() { [ -f "$CFG" ] && command -v jq >/dev/null 2>&1 && jq -r --arg k "$1" '.[$k] // empty' "$CFG" 2>/dev/null; }

TS_LIB_SOURCE="${PERURI_TS_LIB_SOURCE:-$(cfg tsLibSource)}"
TS_LIB_SOURCE="${TS_LIB_SOURCE:-https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib}"

TS_LIB_DEPENDENCY="${PERURI_TS_LIB_DEPENDENCY:-$(cfg tsLibDependency)}"
TS_LIB_DEPENDENCY="${TS_LIB_DEPENDENCY:-file:../peruri-ts-lib}"

echo "ts-lib source:     $TS_LIB_SOURCE"
echo "ts-lib dependency: $TS_LIB_DEPENDENCY"
```

Feed `TS_LIB_DEPENDENCY` into the render PARAMS as `TsLibDependency` (see SKILL.md →
Template Rendering). `package.json.tmpl` writes it verbatim; if the param is omitted the
template falls back to `file:../peruri-ts-lib`, so older callers keep working.

Use `TS_LIB_SOURCE` when the workspace sibling is missing — clone it (`git clone
"$TS_LIB_SOURCE" ../peruri-ts-lib`) rather than hardcoding the URL.

## First-time setup (optional)

The store is optional. To pin a non-default source once:

```bash
mkdir -p ~/.peruri-elysia-scaffolder
cat > ~/.peruri-elysia-scaffolder/config.json <<'JSON'
{
  "tsLibSource": "https://sipgn-git.bgn.go.id/harry.sitohang/peruri-ts-lib",
  "tsLibDependency": "^0.1.0"
}
JSON
```
