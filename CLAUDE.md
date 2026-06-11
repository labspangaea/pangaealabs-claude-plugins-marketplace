# CLAUDE.md — pangaealabs-claude-plugins-marketplace

Maintainer/agent guidance for this repo. This is a **Claude Code plugin marketplace**
by Pangaea Labs. Today it ships one plugin: **`docsmith`** (markdown → on-brand PDFs).

## Layout

| Path | What |
|---|---|
| `.claude-plugin/marketplace.json` | marketplace manifest (owner + plugin list) |
| `plugins/docsmith/` | the shipped plugin — **everything under here installs to users** |
| `plugins/docsmith/skills/make-pdf/` | the only user-facing skill |
| `plugins/docsmith/scripts/` | `build.py`, `doctor.py`, `check_links.py`, etc. |
| `plugins/docsmith/monitors/monitors.json` | background monitors (see below) |
| `plugins/docsmith/references/` | `authoring-guide.md`, `adding-a-template.md` |
| `dev/` | **dev/eval workspaces — NOT shipped** (moved out of `plugins/` on purpose) |
| `dev/docsmith-workspace/trigger-evals.json` | the skill-triggering eval set (20 queries) |

**Never put dev/eval scaffolding under `plugins/docsmith/`** — it would ship to every
user. Keep it in `dev/`. `iteration-*` outputs are git-ignored.

## Monitors (`plugins/docsmith/monitors/monitors.json`)

Both arm on `/make-pdf` and stream signal into the session:
- **`render-log`** — tails `~/.docsmith/render.log` (one OK/FAIL line per build, written by `build.py`).
- **`toolchain-doctor`** — runs `scripts/doctor.py` via `${CLAUDE_PLUGIN_ROOT}` at build
  start to flag a missing/broken toolchain (pandoc/tectonic/rsvg/marp/Chrome), then tails
  `~/.docsmith/toolchain.log`. Catches the **environment** failure class.

`${CLAUDE_PLUGIN_ROOT}` IS available inside a monitor `command` (monitors need Claude Code ≥ v2.1.105).

## Self-healing loop (maintainer commands, NOT shipped to users)

- **`/docsmith-render-triage`** — reads a render FAIL's stderr, classifies **content bug**
  (the user's `.md`) vs **skill/template bug** (docsmith), files an issue only for the latter.
  Default to "content bug"; most failures are the author's document.
- **`/docsmith-fix-loop`** — fixes a *confirmed* docsmith finding, proves it with an
  eval + audit, then PRs. Human-gated; never auto-chained off a failure.

## Three signal systems — DON'T confuse them

These answer different questions and are routinely conflated. Two of them are "evals"
but test completely different things; the third isn't an eval at all.

| System | Question it answers | Renders a PDF? | Inputs | Output |
|---|---|---|---|---|
| **Monitors** (`plugins/docsmith/monitors/monitors.json`) | "what's happening live during a build?" | observes only | the running `/make-pdf` | OK/FAIL + toolchain lines streamed into the session |
| **Triggering eval** (`run_loop.py` / `run_eval.py` / `split_eval_set`) | "does Claude *pick* `make-pdf` for a prompt?" | **NO** | `dev/docsmith-workspace/trigger-evals.json` = `[{query, should_trigger}]` (20 items) + the `make-pdf` `SKILL.md` `description:` | a tuned `description:` (best train/test trigger score) |
| **Output / render eval** (`dev/**/grade.py`, `dev/make-pdf-workspace/grade_run.py`) | "is the produced PDF *correct*?" | **YES** | `dev/make-pdf-workspace/evals.json` = `[{id,name,prompt,assertions,…}]` + rendered run dirs | `grading.json` per run — asserts page size (16:9 `1440x810`, handbook `468x666`), ≥1 embedded image, **no raw `d2` leak**, expected text present |

**Rule of thumb:**
- **Triggering eval = invocation** (does Claude reach for the skill) — *no PDF*. Tuned by `run_loop.py`.
- **Output eval = artifact quality** (is the rendered deck right) — *renders PDFs*. Graded by `grade.py` / `grade_run.py`.
- **Monitors = live telemetry** (not an eval).

`trigger-evals.json` and `evals.json` are **NOT interchangeable** — different schemas, different purpose. `split_eval_set` (stratified train/test holdout) belongs to the *triggering* eval only.

## Skill-description optimizer (`skill-creator` / `run_loop.py`) — READ BEFORE RUNNING

Tunes the `make-pdf` **`description:`** so Claude *triggers* it correctly. It is the
**invocation** decision only — it does **not** render or touch a PDF. Inputs: the eval set
(`dev/docsmith-workspace/trigger-evals.json`), `--skill-path` (the skill's `SKILL.md`),
and `--model`. `run_eval` spawns a real `claude -p` per query×run (live, costs tokens).

**Gotchas (each cost real time/spend to rediscover):**

1. **Do NOT run the trigger eval in-place.** `run_eval` writes a temp command
   `make-pdf-skill-<id>` and only counts a trigger if *that name* is invoked. When docsmith
   is installed in the active env, Claude triggers the **real** `make-pdf` skill instead →
   every should-trigger query **false-negatives**. The in-place run is worthless signal.

2. **Isolation requires a plugin-free config dir — which is NOT authenticated.** Pointing
   `CLAUDE_CONFIG_DIR` at a fresh dir removes docsmith (good) but the nested `claude -p`
   comes back **`Not logged in`** (the keychain token doesn't carry over). You must first run,
   interactively, once: `CLAUDE_CONFIG_DIR=<dir> claude /login`. Only then can the eval run
   isolated + authed.

3. **Do NOT apply the 2026-05-29 optimizer result** (`dev/docsmith-workspace/desc-opt/…/results.json`).
   It is **stale** (describes `bgn-deck` + inline `d2`, both removed) and **low-scoring**
   (4/8 test, never converged). Applying it would regress the current, hand-tuned 0.7.0 description.

**Bottom line:** the shipped `make-pdf` description is already strong; only re-optimize from a
freshly-authed, plugin-free isolated config, and re-baseline against the *current* description
before trusting any "improvement."

## Checks worth knowing

- `scripts/doctor.py` — toolchain presence (exit 1 if a required tool is missing).
- `scripts/check_links.py FILE.pdf [--external]` — post-build link integrity on a *rendered*
  PDF: internal/bookmark dests must resolve (FAIL if dangling); external URIs are syntax-checked
  (placeholder/empty → flagged); `--external` adds opt-in HTTP 404 liveness. Exit non-zero on FAIL.
