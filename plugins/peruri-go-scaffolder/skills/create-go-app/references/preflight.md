# Preflight — `go-peruri-lib` sync + GOPRIVATE gate

This reference holds the two preflight steps the `create-go-app` orchestrator runs **before** collecting any user inputs. The entry-point SKILL.md keeps a short checklist; the exact bash, decision tables, and remediation copy live here.

Both steps fail closed on auth/setup issues. The sync step is best-effort (can be skipped if the user prefers); the GOPRIVATE step is a hard gate because `go mod tidy` will silently fall back to the public proxy without it.

## Table of contents

- [Resolve config store](#resolve-config-store)
- [Sync go-peruri-lib reference clone](#sync-go-peruri-lib-reference-clone)
- [GOPRIVATE prerequisite gate](#goprivate-prerequisite-gate)
- [Lib import mode (git vs local)](#lib-import-mode-git-vs-local)

## Resolve config store

The clone source, GOPRIVATE host, local checkout path, and import mode come from the
config store (`~/.peruri-go-scaffolder/config.json`, layered over `tools/config.env`;
env vars win — full schema in `${CLAUDE_SKILL_DIR}/references/config-store.md`). Source
it once at the start of preflight so every later step uses the resolved values:

```bash
set -a; . "${CLAUDE_SKILL_DIR}/../../tools/config.env"; set +a
echo "host=$PERURI_REMOTE_HOST project=$PERURI_REMOTE_PROJECT mode=$PERURI_GO_LIB_MODE libpath=$PERURI_GO_LIB_PATH"
```

Use `$PERURI_REMOTE_HOST` (not a hardcoded host) in the GOPRIVATE gate, and
`$PERURI_GO_LIB_MODE` to decide whether the generated `go.mod` gets a `replace`
directive (see [Lib import mode](#lib-import-mode-git-vs-local)).

## Sync go-peruri-lib reference clone

In the default `git` mode, generated projects depend on `go-peruri-lib` fetched directly from GitLab via `GOPRIVATE=$PERURI_REMOTE_HOST` — there is **no** `replace` directive — so syncing the local clone only keeps the SKILL.md reference examples current; the scaffolded project still fetches the lib at `go mod tidy` time. In `local` mode the generated `go.mod` gets a `replace` pointing at this clone, so the sync matters for the build too. Either way: sync to keep things current; fail fast on network/auth errors.

Run `${CLAUDE_SKILL_DIR}/../../tools/sync-go-peruri-lib.sh` and read the **first line** of stdout. That single token tells you which branch to take.

| First line | Meaning | Do this |
|---|---|---|
| `PERURI_TOKEN_MISSING` | No env file AND `glab` not authenticated for the host | Run the **first-run token capture** below (prefer the `glab` path), then re-run the script. |
| `CLONED <path>` | Clone was missing; freshly cloned | Continue to Step 1. |
| `UP_TO_DATE <branch> <sha>` | Local already matches `origin/<branch>` | Continue to Step 1. |
| `UPDATE_AVAILABLE <branch>` | Newer commits on `origin/<branch>` exist | Run the **update-available prompt** below. |
| `ERROR: <reason>` | Network, auth, or dirty-tree problem | Show the reason. Ask whether to skip the sync and continue scaffolding against the current state, or stop so the user can fix it. Default offer: skip and continue. |

The sync script resolves credentials in this order, first source wins:

1. `~/.claude/secrets/peruri-gitlab.env` exporting `PERURI_GITLAB_USERNAME` + `PERURI_GITLAB_TOKEN`
2. `glab auth status --hostname sipgn-git.bgn.go.id --show-token` (when the user is logged in to the host via `glab auth login`)

`PERURI_TOKEN_MISSING` only fires when **both** sources fail.

### First-run token capture

Prefer the `glab` path — it leans on the user's existing GitLab CLI session and avoids storing a second copy of the token. Check whether `glab` is installed and authenticated for `sipgn-git.bgn.go.id`:

```bash
glab auth status --hostname sipgn-git.bgn.go.id 2>&1
```

- If the output contains `Logged in to sipgn-git.bgn.go.id as <username>` and `Token found:` — the sync script will pick it up automatically. Just re-run the script.
- If `glab` is missing or not logged in, tell the user verbatim:

> No GitLab credentials found. The sync script can pull credentials in two ways — pick whichever is easier:
>
> **Option A — `glab` CLI (recommended).** If you already use `glab`, run:
>
> ```bash
> brew install glab            # if not installed
> glab auth login --hostname sipgn-git.bgn.go.id
> ```
>
> The sync script will read your username and token directly from `glab`'s config; no second file to manage.
>
> **Option B — env file.** Save credentials at `~/.claude/secrets/peruri-gitlab.env` with mode `600`, outside Claude's auto-memory tree:
>
> ```bash
> mkdir -p ~/.claude/secrets && chmod 700 ~/.claude/secrets
> umask 077
> cat > ~/.claude/secrets/peruri-gitlab.env <<EOF
> PERURI_GITLAB_USERNAME=<username>
> PERURI_GITLAB_TOKEN=<glpat-token>
> EOF
> chmod 600 ~/.claude/secrets/peruri-gitlab.env
> ```
>
> Either way, the personal access token needs at least `read_repository` scope.

Then re-run the sync script. It will clone (if the lib is missing) or proceed to the update check.

### Update-available prompt

When the script prints `UPDATE_AVAILABLE`, the next lines contain `OLD=<sha>`, `NEW=<sha>`, then a `git log --oneline OLD..NEW` block. Show the commit list to the user and ask:

> `go-peruri-lib` has updates on `<branch>`. Update from `<OLD[:8]>` to `<NEW[:8]>`? Skipping is fine — scaffolding will proceed against the current local version.

- **User accepts** → re-run the script. It performs the fast-forward via a temp worktree, leaving the user's active checkout untouched. Confirm the resulting `UPDATED <branch> OLD->NEW` line, then continue to Step 1.
- **User skips** → continue to Step 1 with the current local SHA. Surface this in the final scaffolding summary, e.g. *"Skipped go-peruri-lib update; project wired against `<OLD[:8]>` (newer `<NEW[:8]>` was available)."* The user knows which version they're on and can refresh manually later.

Sync is best-effort. Never block scaffolding on sync failures, network outages, or skipped updates — surface what happened in the summary and let the user decide.

## GOPRIVATE prerequisite gate

Before collecting any other inputs, confirm the local Go environment can reach the private GitLab registry. Run:

```bash
go env GOPRIVATE
```

- If the output **contains** `$PERURI_REMOTE_HOST` (default `sipgn-git.bgn.go.id`) — continue to Step 1.
- If it **does not** — tell the user verbatim (substitute the resolved host):

> `GOPRIVATE` is not set for `$PERURI_REMOTE_HOST`. Scaffolding needs to fetch `go-peruri-lib` from the private GitLab registry. Run:
>
> ```bash
> go env -w GOPRIVATE=$PERURI_REMOTE_HOST
> ```
>
> Go's module fetcher uses Git for private hosts, so it needs Git-level auth for `$PERURI_REMOTE_HOST`. Pick one:
>
> **Option A — reuse `glab` (recommended if `glab auth login` already worked):**
>
> ```bash
> git config --global credential."https://$PERURI_REMOTE_HOST".helper '!glab auth git-credential'
> ```
>
> **Option B — `~/.netrc`:**
>
> ```
> machine $PERURI_REMOTE_HOST login <your-gitlab-username> password <glpat-token>
> ```
>
> Then re-invoke the scaffold.

Do not proceed until the user confirms `GOPRIVATE` is set. This is a hard gate — `go mod tidy` will fail silently or fall back to the public proxy without it.

## Lib import mode (git vs local)

`$PERURI_GO_LIB_MODE` (config-store `libMode`, default `git`) decides how the
**generated** project resolves `go-peruri-lib` — the Go analog of the TS plugin's
`file:` vs git-URL dependency choice:

- **`git` (default)** — no `replace` directive; `go mod tidy` fetches the lib from its
  module path over `GOPRIVATE`. Original behavior; nothing extra to do.
- **`local`** — after `go mod init` in Post-Generation, redirect the module to the local
  checkout so the build resolves against the working tree (no GitLab fetch needed):
  ```bash
  go mod edit -replace "${PERURI_GO_MODULE}=${PERURI_GO_LIB_PATH}"
  go mod tidy
  ```
  Surface the active mode in the final scaffold summary so the user knows whether their
  service is wired to a local checkout or the remote module.
