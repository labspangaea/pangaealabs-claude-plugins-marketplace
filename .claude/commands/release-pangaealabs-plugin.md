Release a new version of one of the plugins in this marketplace: validate, bump the named plugin's version, commit, refresh the marketplace, and update the local install.

This command is project-local — it only appears when Claude Code is launched from this multi-plugin marketplace repo. It is intended for the marketplace maintainer; it is not shipped to teammates via any plugin manifest.

**Arguments:** `$ARGUMENTS`
Expected format: `<plugin-name> <patch|minor|major> "<commit subject>"`

- `<plugin-name>` — must match a directory name under `plugins/`. Examples today: `docsmith`. Run `ls plugins/` to see what's available.
- `<patch|minor|major>`:
  - `patch` (e.g. `0.6.0` → `0.6.1`) — small fix, doc tweak, rule clarification.
  - `minor` (e.g. `0.6.0` → `0.7.0`) — new skill, new command, additive feature.
  - `major` (e.g. `0.6.0` → `1.0.0`) — breaking change to a skill or command interface.
- The commit subject is passed verbatim into `git commit -m`.

---

**Steps:**

### 1. Resolve repo and plugin paths

```bash
REPO=~/projects/pangaealabs-claude-plugins-marketplace
PLUGIN_NAME="<plugin-name from args>"
PLUGIN_DIR="$REPO/plugins/$PLUGIN_NAME"
PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"
MARKETPLACE_NAME="pangaealabs-claude-plugins-marketplace"

# Sanity-check the plugin exists
test -f "$PLUGIN_JSON" || { echo "ERROR: $PLUGIN_JSON not found. Did you mistype the plugin name?"; exit 1; }
```

If the plugin directory or its manifest is missing, stop with a clear error. Don't proceed to bump anything.

### 2. Pre-flight: working tree must contain real edits inside the plugin

```bash
git -C "$REPO" status --porcelain -- "$PLUGIN_DIR"
```

The output MUST contain at least one modified or added file under `plugins/<plugin-name>/` **other than** `.claude-plugin/plugin.json`. If only the manifest is dirty — or nothing under the plugin dir is dirty at all — stop and warn the user: they probably forgot to edit a skill or command, or they typed the wrong plugin name. A no-op version bump is almost never what someone wants.

(Edits outside `plugins/<plugin-name>/` — e.g. to the top-level README, the marketplace.json, or another plugin's files — are fine to coexist and will be staged in the same commit if they relate to this release. Up to your judgment.)

### 3. Read the current version

```bash
python3 -c "
import json
v = json.load(open('$PLUGIN_JSON'))['version']
print('current_version:', v)
"
```

### 4. Compute the new version from the bump arg

For `<patch|minor|major>`, increment the appropriate field and reset lower fields to 0:

| Bump | `0.6.0` becomes |
|---|---|
| patch | `0.6.1` |
| minor | `0.7.0` |
| major | `1.0.0` |

If the bump arg is anything else, stop with an error.

### 5. Edit `plugin.json` to the new version

Use the **Edit** tool on `<PLUGIN_JSON>`. Replace the single `"version": "<old>",` line with `"version": "<new>",`. Do not touch any other field.

### 6. Update the README (if it carries a version)

This marketplace's `README.md` and `marketplace.json` describe plugins in **prose** — there is no per-plugin version cell to bump (unlike a tabular marketplace). So there is normally **nothing to do here**: skip this step.

Only act if you have deliberately added a versioned plugins table or a "current version" badge to `README.md`; in that case, Edit that single version string from `<OLD_VERSION>` to `<NEW_VERSION>` and nothing else. A stale README is never a release blocker.

### 7. Validate the marketplace

```bash
claude plugin validate "$REPO"
```

If validation fails, **revert the version bump** (Edit it back to the previous value) and stop with the validator's error message. Do not commit a manifest the validator rejects.

### 8. Show the user what is about to be committed

```bash
echo "=== status ==="
git -C "$REPO" status
echo ""
echo "=== diff --stat ==="
git -C "$REPO" diff --stat
```

### 9. Confirm before staging and committing

Ask the user explicitly: *"Bump `<plugin-name>` to `<new>` and commit with message: `<commit subject>` ? (yes/no)"*

- If the user replies `yes` (or any clear affirmative — `y`, `ok`, `go`), continue.
- If the user replies anything other than a clear yes (or asks a question), **revert the version bump** with another Edit on `plugin.json` (and the README cell, if you touched one in step 6), leave the rest of their working tree untouched, and stop.

### 10. Stage an explicit file list and commit

```bash
# Pass an explicit space-separated list of modified files; never `git add -A` or `git add .`.
git -C "$REPO" add plugins/$PLUGIN_NAME/.claude-plugin/plugin.json <other-modified-files>

git -C "$REPO" commit -m "<plugin-name>: <commit subject> (<new-version>)

<optional body — leave empty if the user didn't provide one>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
"
```

Prefixing the commit subject with `<plugin-name>:` makes `git log --oneline` readable when multiple plugins live in the same repo.

If the commit fails (e.g. pre-commit hook), surface the error and stop. Do not retry with `--no-verify`. Do not amend a previous commit; create a new one if the user fixes the underlying issue.

### 11. Open a PR (this repo releases via PR into `main`)

This marketplace's `main` is updated through PRs (the maintainer auths to GitHub as the repo owner). Push the release on a branch and open a PR rather than pushing straight to `main`:

```bash
BRANCH="release-$PLUGIN_NAME-<new-version>"
git -C "$REPO" switch -c "$BRANCH"          # if not already on a release branch
git -C "$REPO" push -u origin "$BRANCH"
gh pr create --base main --head "$BRANCH" \
  --title "<plugin-name> <new-version>: <commit subject>" \
  --body "Release <plugin-name> <old> → <new>."
```

If `gh`'s active account can't write to the repo, switch to the owner account first (`gh auth switch --user <owner>`), create the PR, then switch back. If the push fails because the remote diverged, surface the error and stop — do not force-push.

(For a solo maintainer who genuinely wants to release straight to `main`, a plain `git -C "$REPO" push` is acceptable — but never force-push.)

### 12. After the PR merges: refresh the local marketplace from this source

```bash
git -C "$REPO" checkout main && git -C "$REPO" pull --ff-only
claude plugin marketplace update "$MARKETPLACE_NAME"
```

This marketplace is registered as a **directory source** pointing at this repo, so the update reads the local working tree — make sure it is on `main` with the merged release before refreshing.

### 13. Update the installed plugin to the new version

```bash
claude plugin update "$PLUGIN_NAME@$MARKETPLACE_NAME"
```

The output should say `Plugin "<plugin-name>" updated from <old> to <new> for scope user. Restart to apply changes.` If it says "already up to date", the marketplace refresh didn't pick up the new version (often: working tree not on the merged `main`, or the version wasn't actually bumped) — stop and investigate.

### 14. Print a release summary

```
✓ Released <plugin-name> <old> → <new>
   Commit:  <git rev-parse --short HEAD output>
   PR:      <pr url>
   Restart: /exit and re-launch Claude Code to load the new skill bodies into memory.
```

---

**Critical rules:**

- **Always operate on the named plugin only.** If the user passes `docsmith`, only `plugins/docsmith/.claude-plugin/plugin.json` is bumped. Don't touch other plugins' versions.
- **Never use `git add -A` or `git add .`.** Always pass an explicit file list. Multiple plugins coexist in this repo, so a wide stage could pull in unrelated work.
- **Never use `--no-verify`, `--no-gpg-sign`, or any hook-bypass flag.** If a pre-commit hook fails, the answer is to fix the issue, not skip the check.
- **Never force-push.** Step 11 does a plain `git push`; if the push fails due to a diverged remote, surface the error and stop — do not use `--force` or `--force-with-lease`.
- **Never amend a prior commit.** Each release is a new commit on top.
- **If the user declines the confirmation in step 9, revert the version bump on disk** so the working tree is exactly as they left it before invoking `/release-pangaealabs-plugin`. Their other edits stay; only `plugins/<plugin-name>/.claude-plugin/plugin.json` (and any README version cell you touched) returns to the prior value.
- **Stop on validator errors.** A manifest the validator rejects will fail to install, and committing it just creates noise.
- **Do not prune old cache versions** under `~/.claude/plugins/cache/...`. They are harmless; `claude plugin marketplace update` handles cache management.
- **Do not auto-tag releases** (`git tag v<new>`). The `claude plugin tag` subcommand is available if the user wants tags later, but tagging is out of scope here.
