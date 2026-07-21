# Config store — `~/.peruri-go-scaffolder/config.json`

Makes the `go-peruri-lib` **clone source, GOPRIVATE host, local checkout path, and
import mode** configurable without editing the plugin. It layers on top of the
in-repo defaults in `tools/config.env`; every key is optional.

> **Scope (deliberate):** host + clone source + import mode only. The Go **module
> import path** (`sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib`) is baked into
> every generated `.go` file and is **not** a config-store knob — changing it is the
> "rehome" sed operation documented at the top of `tools/config.env`. So `remoteHost`
> changes where the lib is *fetched/cloned from*, not the import path written into source.

## Location & shape

`~/.peruri-go-scaffolder/config.json` (optional):

```json
{
  "remoteHost": "sipgn-git.bgn.go.id",
  "remoteProject": "harry.sitohang/go-peruri-lib",
  "libLocalPath": "~/go/src/sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib",
  "libMode": "git"
}
```

| Key | Maps to | Meaning | Default |
|-----|---------|---------|---------|
| `remoteHost` | `PERURI_REMOTE_HOST` | GitLab host for the token clone URL **and** the GOPRIVATE host. | `sipgn-git.bgn.go.id` |
| `remoteProject` | `PERURI_REMOTE_PROJECT` | `namespace/repo` appended to the host (no `.git`). | `harry.sitohang/go-peruri-lib` |
| `libLocalPath` | `PERURI_GO_LIB_PATH` | Local checkout path — the sync-clone target and the `replace` target in local mode. | `~/go/src/…/go-peruri-lib` |
| `libMode` | `PERURI_GO_LIB_MODE` | `git` or `local` (see below). | `git` |

## Import mode — `git` vs `local`

The Go analog of the TS plugin's `file:` vs git-URL dependency choice:

- **`git` (default)** — generated `go.mod` has **no** `replace`; `go mod tidy` fetches
  the lib from its module path via `GOPRIVATE`. This is the original behavior.
- **`local`** — after `go mod init`, the scaffold adds a `replace` directive so the
  build resolves against your local checkout (the same trick the smoke tool uses):
  ```bash
  go mod edit -replace "${PERURI_GO_MODULE}=${PERURI_GO_LIB_PATH}"
  go mod tidy
  ```

## Precedence (highest wins)

1. Environment variable — `PERURI_REMOTE_HOST`, `PERURI_REMOTE_PROJECT`, `PERURI_GO_LIB_PATH`, `PERURI_GO_LIB_MODE`
2. `~/.peruri-go-scaffolder/config.json`
3. In-repo default in `tools/config.env`

`tools/config.env` performs the layering, so **both** consumers honor it: the bash
sync script (`tools/sync-go-peruri-lib.sh`) and the Go smoke tool (which reads the
exported env vars). Resolve values in preflight by sourcing it:

```bash
set -a; . "${CLAUDE_SKILL_DIR}/../../tools/config.env"; set +a
echo "host=$PERURI_REMOTE_HOST mode=$PERURI_GO_LIB_MODE libpath=$PERURI_GO_LIB_PATH"
```

## First-time setup (optional)

```bash
mkdir -p ~/.peruri-go-scaffolder
cat > ~/.peruri-go-scaffolder/config.json <<'JSON'
{
  "libMode": "local",
  "libLocalPath": "/Users/me/go/src/sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib"
}
JSON
```
