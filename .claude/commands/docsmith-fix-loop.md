Fix a **confirmed** docsmith skill/template/script finding, prove the fix with an eval + audit, and — only if it passes — open a PR that links/closes the issue.

This is a **maintainer** command for the `pangaealabs-claude-plugins-marketplace` repo. It is the *fix → ship* half of the docsmith self-healing loop; the *detect → file* half is `/docsmith-render-triage`, which produces the issue this command consumes. It is reusable for **any** confirmed docsmith finding — from a triage issue, a `check_links.py` report, eval-viewer feedback, or a user report — not just render failures. It is **not** shipped to docsmith users.

**The human gate:** run this **deliberately, on a finding you've confirmed is real.** It mutates code and opens a PR, so it is intentionally a separate, manual step from detection — never chained automatically off a render failure.

**Arguments:** `$ARGUMENTS` — the finding to fix. Preferably a **GitHub issue URL/number** (e.g. `#42`) filed by `/docsmith-render-triage`; otherwise a clear prose description of the bug + where it shows.

---

## Steps

### 1. Resolve the finding

If `$ARGUMENTS` is an issue, read it for the evidence + repro:
```bash
gh issue view <N> --repo labspangaea/pangaealabs-claude-plugins-marketplace --json title,body,number,url
```
Extract: the **template/skill/script** at fault, the **stderr/evidence**, and a **repro** (the failing input or eval sample). If it's a prose finding, restate it as: *what's wrong · where · how to reproduce*. If you can't form a concrete repro, stop and ask — you can't verify a fix you can't reproduce.

### 2. Sync + branch

```bash
REPO=~/projects/pangaealabs-claude-plugins-marketplace
git -C "$REPO" checkout main && git -C "$REPO" pull --ff-only origin main
git -C "$REPO" switch -c fix/docsmith-<short-slug>
```

### 3. Reproduce first

Reproduce the failure on the branch **before** changing anything (render the repro input via `plugins/docsmith/scripts/build.py`, or run `check_links.py`, etc.). You must see the bug to know your fix addresses it. If it doesn't reproduce, say so and stop — the finding may be stale or environment-specific.

### 4. Fix the root cause

Edit the responsible file(s) — a template `theme.css`/`design-system.*`, `build.py`, a `SKILL.md`, `scripts/*`, or `evals/evals.json`. Follow docsmith's conventions and `peruri-code-standard`. Prefer the **minimal** change that fixes the root cause; explain *why* in a comment where the fix is non-obvious. Don't fix the symptom on one slide — fix the rule.

### 5. Eval + audit (the gate — this is mandatory)

Prove no regression and that the bug is gone. Reuse the docsmith eval flow (see `plugins/docsmith/evals/evals.json` and prior `skills/make-pdf-workspace/iteration-*`):

```bash
cd "$REPO/plugins/docsmith"
# Render each eval sample to its template; all must build cleanly:
python3 scripts/build.py --in evals/sample/handbook-sample.md      --out /tmp/fl-hb.pdf --template handbook        --profile evals/sample/profile.yaml
python3 scripts/build.py --in evals/sample/deck-sample.md          --out /tmp/fl-cc.pdf --template claudecode-deck  --profile evals/sample/profile.yaml
python3 scripts/build.py --in evals/sample/corporate-deck-sample.md --out /tmp/fl-co.pdf --template corporate-deck  --profile evals/sample/profile.yaml
```
Then **grade against the assertions** in `evals/evals.json` (page size, embedded SVG via its `<text>` labels — NOT pdfimages, since marp embeds SVG as vector — no ```d2``` leak, footer company, handbook link-check). For a **template-specific** fix, also re-render that template's example under `plugins/docsmith/examples/<template>/`, re-export its `pages/*.png`, and **visually confirm** the specific thing you fixed (render the affected page to PNG and look). Confirm the original repro now **passes**.

> Heavy/parallel eval is a legitimate fan-out (one render per template); a single render is inline. Don't spawn a subagent just to run one build.

**If the eval/audit FAILS or the bug isn't gone:** do NOT open a PR. Report exactly what failed, leave the branch for inspection, and stop (or iterate the fix and re-run step 5).

### 6. Commit + open the PR (only after the gate is green)

Stage an **explicit** file list (never `git add -A`; exclude untracked eval workspaces like `skills/make-pdf-workspace/iteration-*`). Commit (Co-Authored-By line). Then push + open a PR that **links/closes the issue** (auth: `gh auth switch --user labspangaea`, push + `gh pr create`, then switch back to the prior account):

```bash
gh pr create --base main --head fix/docsmith-<short-slug> \
  --title "docsmith: <fix summary>" \
  --body "Fixes the finding in <issue link>. <one-paragraph what+why>. Eval+audit green: <summary>.

Closes #<N>"
```
`Closes #<N>` auto-closes the triage issue when the PR merges — completing the loop `triage issue → fix → eval → PR ↔ issue`.

### 7. Report

Print: the finding, the fix (files + one-line why), the **eval/audit result** (pass/fail per assertion), the **PR URL**, the linked issue, and confirmation the active gh account was restored. If the gate failed, report that instead — no PR.

---

**Guardrails (the why):**
- **The eval gate is non-negotiable.** A fix that isn't proven green doesn't ship — that's the whole point of closing the loop through eval, not just "looks fixed."
- **Reproduce before and verify after.** A fix you can't reproduce is a guess; a fix you didn't re-verify is a regression risk.
- **One finding per run.** Keeps the PR reviewable and the issue link clean.
- **Human-gated by design.** This runs on a *confirmed* finding you chose to fix — never auto-triggered. Detection (`/docsmith-render-triage`) and shipping (this) are deliberately separate so a person decides what's worth fixing.
- **Explicit staging, never force-push, restore the gh account.** Same release-hygiene rules as `/release-pangaealabs-plugin`.
- **Don't bump the plugin version here** — that's `/release-pangaealabs-plugin`'s job; note in the PR if a release is warranted once merged.
