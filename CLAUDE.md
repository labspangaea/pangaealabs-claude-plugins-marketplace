# CLAUDE.md — pangaealabs-claude-plugins-marketplace

Maintainer/agent guidance for this repo. This is a **Claude Code plugin marketplace**
by Pangaea Labs. Today it ships six plugins: **`docsmith`** (markdown → on-brand PDFs),
**`testcraft`** (user flows → test-case suite + offline HTML console), **`dkv`**
(graphic-design fundamentals → design critique + direction), the two scaffolders
**`go-scaffolder`** / **`elysia-scaffolder`**, and **`claude-profiles`** (two Claude
subscriptions on one machine, sharing one config).

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
| `plugins/testcraft/` | second plugin — **user flows → test cases**; everything under here installs to users |
| `plugins/testcraft/skills/{testcase-importer,userflow-to-testcases}/` | the two user-facing skills (each `SKILL.md` + `scripts/` + `references/`) |
| `plugins/testcraft/agents/` | `testcase-architect`, `testcase-vapt-auditor` subagents (self-contained — no project-`CLAUDE.md` dependency) |
| `plugins/dkv/` | third plugin — **graphic-design fundamentals**; knowledge + one script, no assets/agents |
| `plugins/dkv/skills/design-fundamentals/scripts/contrast.py` | WCAG ratios + verdict per threshold. **`ui` (3:1, non-text) is the case reviews miss** — a label can pass at 13:1 while its border fails at 2:1. Has `--selfcheck`. |
| `plugins/dkv/skills/design-fundamentals/` | the only user-facing skill (`SKILL.md` router + rubric) |
| `plugins/dkv/skills/design-fundamentals/references/` | `color.md`, `typography.md`, `layout.md`, `gestalt.md`, `principles.md` — section-numbered so `SKILL.md` cites `§N`. **`principles.md` is an index, not a peer doc** — contrast/hierarchy/repetition live where they're operationalised; don't restate them there. |
| `plugins/{go-scaffolder,elysia-scaffolder}/` | the two service scaffolders (5 skills each) |
| `plugins/claude-profiles/` | sixth plugin — **multi-subscription setup**; one skill, three python3 scripts, no assets/agents |
| `plugins/claude-profiles/skills/setup-claude-profiles/scripts/` | `profiles_doctor.py` (read-only report + `--selfcheck`), `link_shared_config.py` (dry-run-first symlink sharing, reversible), `sync_mcp.py` (mirrors `mcpServers`), `shell_wrapper.py` (registers the per-profile launcher in `~/.zshrc`/`~/.bashrc`). Shared helpers in `_profiles.py`. |
| `dev/claude-profiles-workspace/test_*.py` / `test_*.mjs` | the test suite — `python3 -m unittest discover -s dev/claude-profiles-workspace -p 'test_*.py'` (35 unit tests) and `node dev/claude-profiles-workspace/test_wizard.mjs /tmp/wiz` (installer wizard, end to end). Both run against a temporary HOME and assert the real profiles are untouched. |
| `dev/` | **dev/eval workspaces — NOT shipped** (moved out of `plugins/` on purpose) |
| `dev/docsmith-workspace/trigger-evals.json` | the skill-triggering eval set (20 queries) |

**Never put dev/eval scaffolding under `plugins/docsmith/`** — it would ship to every
user. Keep it in `dev/`. `iteration-*` outputs are git-ignored.

## `testcraft` (second plugin — user flows → test cases)

`plugins/testcraft/` ships two chained skills + two subagents that turn a user-flow doc into an
importer-ready test-case CSV and an offline HTML console:

- **`userflow-to-testcases`** — authors cases *from* a flow (state machines → per-transition
  cases with downstream impact → actor×resource matrix → E2E → VAPT). Stops at the CSV.
- **`testcase-importer`** — normalizes *existing* case data (xls/xlsx, CSV/TSV, PDF, pasted/md)
  into the canonical CSV, then renders the console (`scripts/render_console.py`).
- agents **`testcase-architect`** / **`testcase-vapt-auditor`** for heavy authoring + the
  security pass.

Self-contained, unlike docsmith: each skill bundles its own `scripts/` + `references/`, and the
agents carry the full method inline (no project-`CLAUDE.md` dependency), so the plugin is
portable. The **canonical CSV (10 cols)** — `ID, Group, Type, Outcome, Priority,
Severity_Reasoning, Transition, Title, Steps / Test Data, Expected Result + Downstream Impact /
Fix` — is the interchange format between both skills and the console; the bundled
`validate_cases.py` is the importer-ready gate. No monitors/evals ship here — testcraft's eval
workspaces live in its originating project, not this repo.

## `claude-profiles` (sixth plugin — two subscriptions, one machine)

`plugins/claude-profiles/` ships one skill, `setup-claude-profiles`, and three stdlib-only Python
scripts. The domain facts it encodes were verified against a real two-subscription macOS setup; the
WSL paths are covered by `profiles_doctor.py --selfcheck`, which drives the filesystem detection
from a captured `/proc/mounts` table so the WSL logic is exercised on a non-WSL box.

**Four facts the plugin exists to get right — don't "simplify" any of them away:**

1. The default profile's live config is **`~/.claude.json`**, NOT `~/.claude/.claude.json` (which
   commonly exists as a stale leftover and reports the wrong account). Only
   `_profiles.config_json_for()` may resolve this.
2. `mcpServers` is a key of `.claude.json` and is **not** valid in `settings.json` — putting it
   there is silently ignored. That is why `sync_mcp.py` copies rather than linking.
3. Claude Code writes **through** a symlinked `settings.json` instead of replacing it, which is what
   makes the whole sharing scheme work. Verified, not assumed.
4. The marketplace registry is split between `settings.json` (`extraKnownMarketplaces`) and the
   per-profile `plugins/known_marketplaces.json` — so `plugins/` must be shared as a whole
   directory, or plugins from a marketplace known only to the first profile vanish with no error.

`link_shared_config.py` is dry-run by default and backs up anything it displaces into
`<target>/backups/profile-link-<ts>/`; `--unlink --apply` restores from there. Keep both properties.

**A clack `placeholder` is a VALUE, not a hint.** `@clack/core` writes the placeholder verbatim
into the field when Tab is pressed on an empty input, so any descriptive text in one becomes a real
value. A placeholder reading `work   →  ~/.claude-work` created a directory of that exact name on a
user's machine. Put the explanation in `message:`; keep `placeholder:` to something the user could
legitimately have typed. `installer/profiles.mjs` exports `profilePlaceholder()` and
`invalidProfileInput()` for this, covered by `dev/claude-profiles-workspace/test_profile_input.mjs`.

**`shell_wrapper.py` is the canonical rc writer, and it must stay in the PLUGIN.** The `npx`
installer's wizard calls it and so does step 4 of the skill — someone who installs with
`/plugin install` never runs the installer, so logic that lived only there would mean the launcher
silently never gets registered on their machine. Same reason docsmith has one `setup_profile.py`.

**`_profiles.config_dir()` strips whitespace, and that is load-bearing.** A trailing space created
a real `.claude-work  ` directory on a fresh install; a leading space is worse, because
`expanduser` leaves `" ~/..."` alone so the path stops being absolute and resolves against the
cwd — creating a folder literally named `~`. `unusable_profile_dir()` is the backstop for names
that survive stripping and still cannot be typed back. Both are covered in
`dev/claude-profiles-workspace/test_shell_wrapper.py`; write the failing test before the fix.

## `dkv` (third plugin — design theory → critique + direction)

`plugins/dkv/` ships one skill, `design-fundamentals`, and no code. `SKILL.md` is a router + review
rubric; five section-numbered reference files hold the theory, and only the relevant one or two are
ever read.

**The sourcing convention is load-bearing — don't strip it when editing.** Unmarked statements are
ordinary craft convention (each file says so at the top). Two things are marked inline:

- **`⚠ contested`** — popular but weakly supported, with what's actually known. There are exactly
  four: φ as a law of beauty (Zeising/Devlin), pink lowering heart rate (Baker-Miller, failed
  replication), the 80% brand-recognition figure (miscited Hoadley 1990), and 60/30/10's empirical
  status. Removing these tags is how the plugin becomes just another confident design-folklore
  repeater, which is the exact failure mode it exists to avoid.
- **citations** — wherever a specific number does the work (WCAG ratios, 45–75 measure,
  NN/g scan patterns, Müller-Brockmann, Paoletti).

`gestalt.md` covers the full canonical set of ten grouping laws, including Prägnanz, common region
and uniform connectedness — §11's strength ordering (connectedness > region > proximity >
similarity) is the part a critique actually needs, so keep it if the file is ever trimmed.

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
- **Two post-install wizards, same division of labour.** `installer/profile.mjs` (docsmith)
  and `installer/profiles.mjs` (claude-profiles) hold only the clack UI; every filesystem
  decision is delegated to the plugin's own scripts, so install-time and in-agent setup
  cannot drift. `profiles.mjs` never invents a plan — it runs `link_shared_config.py`'s real
  dry run, shows that output, asks once, then re-runs the same command with `--apply`. It
  supports **more than two** profiles (loop until "add another?" is declined), leaves the
  default `~/.claude` in place, and refuses to run without a TTY. `--no-profile` skips both.
  Verify: `node installer/index.mjs add claude-profiles -g --symlink -a claude-code --dry-run`
  (the no-TTY guard fires) and the harness pattern in `dev/claude-profiles-workspace/`.
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
  -a claude-code,codex --no-profile --dry-run`. For a **multi-skill** plugin, pre-select skills
  with `-s` so it doesn't block on the skill multiselect:
  `node installer/index.mjs add testcraft -s testcase-importer,userflow-to-testcases -g --symlink
  -a claude-code,codex --dry-run`. Flags: `add <plugin>`, `-s/--skill` (names, comma-sep;
  required to install a multi-skill plugin headlessly), `-a/--agent`, `-g/--global`, `--project`,
  `--copy/--symlink`, `--no-profile`, `--dry-run`, `-y`.

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
   separate shadowing vectors.

   > **Why the config vector is broader than it looks (learned 2026-07-29, cost ~45 min of invalid
   > runs).** It is tempting to reason "the skill under test isn't installed, so nothing can shadow
   > it, so I can skip `CLAUDE_CONFIG_DIR`." **That is wrong.** Shadowing comes from *any* installed
   > skill that competes for the same queries, not from the same-named one. A dkv trigger eval run
   > against the normal config scored 1/10 and 0/10 recall on two very different descriptions —
   > because `impeccable`, `frontend-design`, `high-end-visual-design`, `design-taste-frontend`,
   > `stitch-design-taste`, `brandkit` and friends are installed and get selected for design
   > queries instead of the stub. The detector counts only the stub token, so every correct
   > selection records as a miss. A docsmith **control** run (its own description + its own eval
   > set, where `CLAUDE.md` records 7/10) scored **0/10** in the same conditions, which is what
   > proved the runs invalid rather than the descriptions bad. Always run the control first — if a
   > known-good description doesn't reproduce its recorded score, stop and fix the environment
   > before reading any numbers.
   >
   > Note `/login` may be unavailable in some environments (it is not a slash command in every
   > build), in which case the isolated config cannot be authed and **the triggering eval simply
   > cannot be run there.** Say so rather than reporting the uncontrolled numbers.
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
