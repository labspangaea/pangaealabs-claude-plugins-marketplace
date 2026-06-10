Triage a docsmith render **failure**: read the captured error, decide whether it's a *content* bug (the source document) or a *skill/template* bug (docsmith itself), and — only for a genuine skill/template bug — open a GitHub issue with the error as evidence.

This is a **maintainer** command for the `pangaealabs-claude-plugins-marketplace` repo. It is the *detect → file* half of the docsmith self-healing loop; the *fix → ship* half is `/docsmith-fix-loop`, which consumes the issue this command files. It is **not** shipped to docsmith users — end users get inline error help from the `make-pdf` skill while it builds.

**Where the evidence comes from:** the docsmith render-log monitor (`plugins/docsmith/monitors/monitors.json`) tails `~/.docsmith/render.log`, where `build.py` writes one line per build. A failure looks like:
```
22:27:35 FAIL handbook (rc=43) /tmp/x.pdf [err: ~/.docsmith/render-errors/20260610-222735-handbook.log]
```
The `[err: …]` file holds the backend's (pandoc/tectonic/marp) **stderr tail** — the actual root cause.

**Arguments:** `$ARGUMENTS` — optional. A specific error-log path, a render-log FAIL line, or empty (then triage the **most recent** FAIL in `~/.docsmith/render.log`).

---

## Steps

### 1. Locate the failure + its evidence

```bash
LOG="$HOME/.docsmith/render.log"
# Most recent FAIL line (or use the one passed in $ARGUMENTS):
tail -n 50 "$LOG" | grep " FAIL " | tail -n 1
```

Parse the line for: `template`, `rc`, the output path, and the `[err: <path>]` reference. **Read the `[err: …>` file** — that stderr tail is your primary evidence. If there is no `[err: …]` (older log line, or the error file was cleaned up), you have only the exit code; say so and ask whether to re-run the build to capture fresh stderr rather than guessing.

If there is **no FAIL line at all**, report that there's nothing to triage and stop.

### 2. Read the source document that failed

The render-log line has the *output* path, not the source. If you can't identify the source `.md` from context, ask the user which document produced this failure. Read it (and any SVG/asset it references) — you cannot classify a failure without seeing what was fed in.

### 3. Classify: content bug vs skill/template bug

This is the crucial judgment — **most render failures are content bugs, not docsmith bugs.** Use the stderr + the source:

| Signal | Likely **content** bug (fix the doc — do NOT file an issue) |
|---|---|
| `Undefined control sequence` from raw LaTeX the **author wrote** | author's `\command` typo / unescaped `\` |
| `could not fetch resource` / missing file | a diagram/logo path in the doc doesn't exist |
| Malformed SVG that fails `rsvg-convert` | the hand-authored SVG is broken |
| marp "no such class" from a `<!-- _class: typo -->` | author typo'd a class name |

| Signal | Likely **skill/template** bug (file an issue) |
|---|---|
| LaTeX/CSS error originating in the **generated** preamble / `_tokens.tex` / theme.css | a template or `build.py` produced invalid output |
| A documented class/callout renders broken on a **minimal, correct** input | the template is broken |
| `build.py` traceback / crash (not a backend error) | a script bug |
| The same failure reproduces across **different** users' valid documents | systematic, not one-off |

When unsure, **reproduce on a minimal correct input** for that template (an eval sample under `plugins/docsmith/evals/sample/` is ideal): if a clean sample fails too, it's a skill/template bug; if only the user's doc fails, it's content.

### 4a. Content bug → help, don't file

Do **not** open an issue (one-off content bugs would be noise). Instead, explain the root cause in plain terms, quote the offending line, and tell the user exactly how to fix their document — point them at `plugins/docsmith/references/authoring-guide.md` for the relevant rule. Stop here.

### 4b. Skill/template bug → confirm, dedupe, then file an issue

1. **Dedupe.** Check for an existing open issue first so you don't file a duplicate:
   ```bash
   gh issue list --repo labspangaea/pangaealabs-claude-plugins-marketplace --state open --search "docsmith <template> <short error phrase>"
   ```
   If a matching issue exists, add a comment with this occurrence's evidence instead of opening a new one.
2. **Confirm with the user** before filing — show your classification + the evidence and ask *"File a docsmith issue for this skill/template bug? (yes/no)"*. A skill/template bug is a real claim; don't auto-file on a hunch.
3. **File the issue** (auth: the repo is owned by `labspangaea`; if `gh`'s active account can't write, `gh auth switch --user labspangaea`, file, then switch back):
   ```bash
   gh issue create --repo labspangaea/pangaealabs-claude-plugins-marketplace \
     --title "docsmith/<template>: <one-line root cause>" \
     --label "docsmith,bug" \
     --body "<body below>"
   ```
   Issue body must contain, as evidence:
   - the render-log **FAIL line** (verbatim),
   - the **stderr tail** from the `[err: …]` file (in a fenced block),
   - the **template** and a minimal **repro** (the failing input, or the eval sample that reproduces it),
   - your **classification reasoning** (why this is a skill/template bug, not content).

   Always restore the gh active account afterward.

### 5. Report

Print: the classification (content vs skill/template), the evidence summary, and — if filed — the **issue URL** (which is the input to `/docsmith-fix-loop`). If it was a content bug, print the fix guidance instead.

---

**Guardrails (the why):**
- **Default to "content bug."** A render FAIL almost always means the author's document was wrong, not docsmith. Filing an issue per one-off content error would bury real bugs in noise — so the bar for filing is "reproduces on a minimal *correct* input" or "the error is in docsmith's generated output."
- **Never auto-file.** Always confirm; a filed issue asserts docsmith is broken.
- **Always dedupe** before filing.
- **Evidence, not vibes.** The issue must carry the actual stderr + a repro, so `/docsmith-fix-loop` has something concrete to work from.
- **This command never edits code or opens PRs.** It only reads, classifies, and (with consent) files an issue. Fixing is `/docsmith-fix-loop`'s job, behind a human gate.
