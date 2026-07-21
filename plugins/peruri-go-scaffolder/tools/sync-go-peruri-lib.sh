#!/usr/bin/env bash
# Sync ~/go/src/.../go-peruri-lib against origin/main (fallback master).
#
# Credential resolution (first source that produces a token wins):
#   1. ~/.claude/secrets/peruri-gitlab.env exporting PERURI_GITLAB_USERNAME + PERURI_GITLAB_TOKEN
#   2. `glab auth status --hostname <host> --show-token` (requires `glab` CLI logged in to the host)
# If neither path yields a token, prints PERURI_TOKEN_MISSING and exits 2.
#
# stdout contract — the SKILL.md dispatch table reads the FIRST LINE only:
#   PERURI_TOKEN_MISSING        no env file AND glab not authenticated for the host
#   CLONED <path>               clone was missing; cloned successfully
#   UP_TO_DATE <branch> <sha>   already current
#   UPDATE_AVAILABLE <branch>   newer commits exist; OLD/NEW + commit list follow
#   UPDATED <branch> OLD->NEW   update was applied (after a re-run with no --check)
# Errors go to stderr prefixed `ERROR:` and the script exits non-zero.
#
# Exit codes:
#   0 = clean (cloned, up-to-date, or update applied)
#   1 = update needed but caller asked --check; no modifications made
#   2 = hard error (token missing, fetch failed, dirty tree blocks ff, branch missing)

set -euo pipefail

# Load the plugin's central config (paths + URLs). Each value uses
# `${VAR:-default}` so an existing environment override wins; otherwise the
# defaults in tools/config.env apply. See that file for the migration recipe
# when the package URL changes.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/config.env"

LIB="$PERURI_GO_LIB_PATH"
REMOTE_HOST="$PERURI_REMOTE_HOST"
REMOTE_PATH="$PERURI_REMOTE_PROJECT"
ENV_FILE="$HOME/.claude/secrets/peruri-gitlab.env"

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) ;;
  esac
done

# Phase A — credentials (env file preferred, glab CLI as fallback)
PERURI_GITLAB_USERNAME=""
PERURI_GITLAB_TOKEN=""
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; . "$ENV_FILE"; set +a
fi

if [ -z "${PERURI_GITLAB_USERNAME:-}" ] || [ -z "${PERURI_GITLAB_TOKEN:-}" ]; then
  if command -v glab >/dev/null 2>&1; then
    GLAB_OUT=$(glab auth status --hostname "$REMOTE_HOST" --show-token 2>&1 || true)
    GLAB_USER=$(printf '%s\n' "$GLAB_OUT" | sed -nE 's/.*Logged in to .* as ([^ ]+).*/\1/p' | head -n1)
    GLAB_TOKEN=$(printf '%s\n' "$GLAB_OUT" | sed -nE 's/.*Token found: (glpat-[A-Za-z0-9._-]+).*/\1/p' | head -n1)
    if [ -n "$GLAB_USER" ] && [ -n "$GLAB_TOKEN" ]; then
      PERURI_GITLAB_USERNAME="$GLAB_USER"
      PERURI_GITLAB_TOKEN="$GLAB_TOKEN"
    fi
  fi
fi

if [ -z "${PERURI_GITLAB_USERNAME:-}" ] || [ -z "${PERURI_GITLAB_TOKEN:-}" ]; then
  echo "PERURI_TOKEN_MISSING"
  exit 2
fi
TOKEN_URL="https://${PERURI_GITLAB_USERNAME}:${PERURI_GITLAB_TOKEN}@${REMOTE_HOST}/${REMOTE_PATH}.git"

# Phase B — clone if missing
if [ ! -d "$LIB/.git" ]; then
  if [ "$CHECK_ONLY" = "1" ]; then
    echo "ERROR: lib not present at $LIB and --check forbids clone" >&2
    exit 2
  fi
  mkdir -p "$(dirname "$LIB")"
  # --quiet keeps progress off stdout so the dispatch table stays parseable
  git clone --quiet "$TOKEN_URL" "$LIB"
  echo "CLONED $LIB"
  exit 0
fi

# Phase C — detect default branch (main → master)
if git -C "$LIB" show-ref --verify --quiet refs/heads/main; then
  BRANCH=main
elif git -C "$LIB" show-ref --verify --quiet refs/heads/master; then
  BRANCH=master
else
  echo "ERROR: neither 'main' nor 'master' branch exists in $LIB" >&2
  exit 2
fi

# Phase D — refresh remote URL with token form (idempotent)
git -C "$LIB" remote set-url origin "$TOKEN_URL"

# Phase E — worktree-based check & update
WT=$(mktemp -d "${TMPDIR:-/tmp}/glplib-sync-XXXXXX")
cleanup() {
  git -C "$LIB" worktree remove --force "$WT" >/dev/null 2>&1 || true
  rm -rf "$WT"
}
trap cleanup EXIT

# Detached worktree at the local branch's current tip — safe even if main
# checkout is on the same branch (avoids "branch already checked out").
git -C "$LIB" worktree add --detach --quiet "$WT" "$BRANCH"

OLD=$(git -C "$WT" rev-parse HEAD)
if ! git -C "$WT" fetch --quiet origin "$BRANCH"; then
  echo "ERROR: fetch failed for origin/$BRANCH (network or auth)" >&2
  exit 2
fi
NEW=$(git -C "$WT" rev-parse "origin/$BRANCH")

if [ "$OLD" = "$NEW" ]; then
  echo "UP_TO_DATE $BRANCH ${OLD:0:8}"
  exit 0
fi

# Update available — emit summary on stdout (model parses these lines)
echo "UPDATE_AVAILABLE $BRANCH"
echo "OLD=$OLD"
echo "NEW=$NEW"
echo "--- commits ---"
git -C "$WT" log --oneline "$OLD..$NEW"
echo "--- end ---"

if [ "$CHECK_ONLY" = "1" ]; then
  exit 1
fi

# Apply: strategy depends on whether main checkout is on $BRANCH
CURRENT=$(git -C "$LIB" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "DETACHED")
if [ "$CURRENT" = "$BRANCH" ]; then
  if ! git -C "$LIB" diff-index --quiet HEAD --; then
    echo "ERROR: $LIB has uncommitted changes on $BRANCH; refusing to update" >&2
    exit 2
  fi
  git -C "$LIB" merge --ff-only --quiet "origin/$BRANCH"
else
  # Main checkout is on a different branch — fast-forward the branch ref directly
  git -C "$LIB" branch -f "$BRANCH" "origin/$BRANCH"
fi
echo "UPDATED $BRANCH ${OLD:0:8} -> ${NEW:0:8}"
