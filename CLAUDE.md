# CLAUDE.md — pangaealabs-claude-plugins-marketplace

Maintainer/agent guidance for this repo. This is a **Claude Code plugin marketplace**
by Pangaea Labs. Today it ships one plugin: **`docsmith`** (markdown → on-brand PDFs).

## Layout

| Path | What |
|---|---|
| `.claude-plugin/marketplace.json` | marketplace manifest (owner + plugin list; each plugin may declare a `skills:` array) |
| `installer/` | **`npx` installer CLI** (`index/marketplace/agents/install/profile.mjs`) — the `npx github:…` entry; installs skills into **any** agent. **NOT** part of the Claude plugin payload. See "The `npx` installer" below. |
| `package.json` / `package-lock.json` | declares the installer `bin` so `npx github:…` runs (no npm publish needed); dep `@clack/prompts` |
| `docs/install.md` | end-user install docs (native `/plugin` path **and** the `npx` cross-agent path) |
| `plugins/docsmith/` | the shipped plugin — **everything under here installs to users** |
| `plugins/docsmith/skills/make-pdf/` | the only user-facing skill |
| `plugins/docsmith/scripts/` | `build.py`, `doctor.py`, `check_links.py`, `marp_prep.py`, `setup_profile.py` (canonical `profile.yaml` writer — interactive + `--json`) |
| `plugins/docsmith/monitors/monitors.json` | background monitors (see below) |
| `plugins/docsmith/references/` | `authoring-guide.md`, `adding-a-template.md` |
| `plugins/docsmith/assets/templates/` | design-system templates (`handbook`, `corporate-deck`, `claudecode-deck`, `kawaii-storybook`, `concept-deck`). **`concept-deck`** is **SVG-first / tech-doc** — one full-canvas SVG per concept; author its diagrams per `concept-deck/icons.md` (the SVG-DNA generation guide). |
| `dev/` | **dev/eval workspaces — NOT shipped** (moved out of `plugins/` on purpose) |
| `dev/docsmith-workspace/trigger-evals.json` | the skill-triggering eval set (20 queries) |

**Never put dev/eval scaffolding under `plugins/docsmith/`** — it would ship to every
user. Keep it in `dev/`. `iteration-*` outputs are git-ignored.

## The `npx` installer (`installer/` — cross-agent install, NOT the Claude plugin)

Beyond `/plugin marketplace add …`, the repo ships an interactive `npx` installer so
docsmith's skills run in **any** agent (Claude Code, OpenClaw, Hermes, Cursor, Codex,
OpenCode, Gemini CLI, …), not just Claude Code:

```
npx github:labspangaea/pangaealabs-claude-plugins-marketplace
```

- **Entry:** root `package.json` `bin` → `installer/index.mjs` (so `npx github:…` works
  with **no npm publish**). Only dep is `@clack/prompts` (the skills.sh TUI look).
- **Flow:** plugins (`marketplace.json`) → skills (`SKILL.md` frontmatter) → agents
  (`installer/agents.mjs` registry) → scope → method → summary/confirm → install →
  docsmith profile wizard.
- **Universal-store model** (`installer/install.mjs` + `agents.mjs`): the skill is written
  ONCE to `~/.agents/skills/<skill>` (global) or `./.agents/skills/<skill>` (project), then
  symlinked (or copied) into each agent's own dir. Agents that already read `~/.agents/skills`
  (Codex, OpenCode, Gemini CLI, Copilot, Amp, Warp, Zed, Cline) need no extra link.
- **Relocatable bundle:** the installer copies `scripts/`, `assets/`, `references/` (+
  `examples/profile.example.yaml`) INTO the skill dir so it's self-contained. `build.py`
  resolves its plugin root as `__file__/../..`, so it runs unchanged from the relocated
  location. Plugin-only bits (`monitors/`, `agents/`) are deliberately **not** bundled —
  they're Claude-Code machinery, inert in a bare skill. (Hence `SKILL.md`'s `PLUGIN_DIR`
  note now resolves both the plugin layout and the standalone `~/.agents/skills` layout.)
- **One canonical profile writer:** `scripts/setup_profile.py` (pure-stdlib to write; PyYAML
  only for append). The installer's clack wizard (`installer/profile.mjs`) collects fields then
  pipes JSON to `setup_profile.py --json`; the **same** script is `make-pdf` **Step 0**. So
  install-time and in-agent setup are byte-identical, and non-Claude agents (no
  `AskUserQuestion`) still get a working `~/.docsmith/profile.yaml`. The 8 org fields:
  `company, author, email, logo, wordmark, website, default_confidentiality, copyright`.
  - **Gotcha (already bitten):** `profile.mjs` MUST spawn the writer with
    `env: { ...process.env, ...env }`. If it inherits the bare process env, the writer
    resolves a different `$DOCSMITH_HOME` than the wizard reported and writes to the wrong
    place — e.g. clobbering the real `~/.docsmith/profile.yaml` during a sandboxed test.
- **`installer/`, `package.json`, `package-lock.json`, `docs/` are repo tooling — NOT the
  Claude plugin payload.** They never install via `/plugin`; only `plugins/docsmith/` does.
  `node_modules/` is git-ignored.
- **Verify non-interactively:** `node installer/index.mjs add docsmith -g --symlink
  -a claude-code,codex --no-profile --dry-run`. Flags: `add <plugin>`, `-a/--agent`,
  `-g/--global`, `--project`, `--copy/--symlink`, `--no-profile`, `--dry-run`, `-y`.

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

2. **Isolation needs BOTH a plugin-free config AND a cwd far from the repo** — there are two
   separate shadowing vectors:
   - **Config:** point `CLAUDE_CONFIG_DIR` at a fresh dir (no installed plugins). A fresh dir
     is **not authed** (the keychain token doesn't carry over) — run, interactively, once:
     `CLAUDE_CONFIG_DIR=<dir> claude /login`.
   - **cwd:** run the eval from a throwaway dir (e.g. `/tmp/…`), **never from or under the
     marketplace checkout** — otherwise the nested `claude -p` picks up docsmith as a
     *project-local* skill and shadowing returns even with a clean config.

3. **`run_eval`'s detector under-counts on Claude Code 2.1.x — the stub DOES trigger.**
   The earlier "command stubs don't fire in 2.1.x" conclusion was **wrong** (verified with
   `--include-partial-messages` traces): the `.claude/commands/make-pdf-skill-<id>` stub
   registers fine and Claude *does* select it. The bug is in the harness's stream detector,
   which calls a query a **miss** the instant it sees the first `message_stop` (or the first
   tool that isn't `Skill`/`Read`). But on CC 2.1.x the model **inspects the input file in
   turn 1 and selects the skill in turn 2** — so the detector bails *before* the selection and
   reports an all-negative artifact. Fix: scan **all** turns and only conclude "not triggered"
   at the top-level `result` event (don't terminate on `message_stop`; don't hard-fail on a
   leading non-Skill tool). A corrected, drop-in harness lives at
   **`dev/docsmith-workspace/run_trigger_eval.py`** (the minimal upstream diff for
   `skill-creator/run_eval.py` is in `dev/docsmith-workspace/run_eval.py.patch`).

**Bottom line:** with the corrected harness the triggering eval **does** produce trustworthy
signal here. Last run (shipped description, `sonnet`, 2 runs/query, fully isolated):
**no-trigger specificity 10/10** (zero over-trigger) and **should-trigger recall 7/10 raw** —
where all 3 raw misses are *underspecified* eval queries ("this content" / "these notes" with
nothing attached) that flip to **6/6** the moment the referenced input file is present. The
shipped `make-pdf` description is strong and needs no change; re-run via `run_trigger_eval.py`
(not the stock `run_eval.py`) if you tune it, and seed the referenced input files first so
recall isn't masked by the model pausing to ask for missing input.

## Checks worth knowing

- `scripts/doctor.py` — toolchain presence (exit 1 if a required tool is missing).
- `scripts/check_links.py FILE.pdf [--external]` — post-build link integrity on a *rendered*
  PDF: internal/bookmark dests must resolve (FAIL if dangling); external URIs are syntax-checked
  (placeholder/empty → flagged); `--external` adds opt-in HTTP 404 liveness. Exit non-zero on FAIL.
