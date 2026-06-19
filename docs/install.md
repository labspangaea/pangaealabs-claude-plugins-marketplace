# Installing the Pangaea Labs marketplace with `npx`

Two ways to install, depending on which agent you use.

## A. Claude Code (native plugins)

```text
/plugin marketplace add labspangaea/pangaealabs-claude-plugins-marketplace
/plugin install docsmith
```

This installs the full **plugin** — skill + background monitors + subagents.

## B. Any agent (`npx` installer)

For Claude Code **and** other agents (OpenClaw, Hermes, Cursor, Codex, OpenCode,
Gemini CLI, GitHub Copilot, Warp, Zed, …), run the interactive installer:

```text
npx github:labspangaea/pangaealabs-claude-plugins-marketplace
```

It walks you through the same flow as the screenshots you've seen from `skills.sh`:

1. **Plugins** — pick which marketplace plugins to install.
2. **Skills** — pick which skills inside them (today: `make-pdf`).
3. **Agents** — pick which agents to install into (Claude Code is pre-checked).
4. **Scope** — Global (`~`, all projects) or Project (current dir).
5. **Method** — Symlink (recommended) or Copy.
6. **Summary + confirm.**
7. **docsmith profile wizard** — set up `~/.docsmith/profile.yaml` (company, author,
   email, logo, wordmark, website, confidentiality, copyright) for one or more orgs.

Useful flags:

```text
npx github:labspangaea/...  add docsmith        # pre-select a plugin
                            -g | --global       # install for all projects
                            --project           # install into the current dir
                            --copy | --symlink  # placement method
                            --dry-run           # show the plan; write nothing
                            -y | --yes          # skip the final confirm
```

### How cross-agent install works (the "universal store" model)

The skill payload is written **once** to a universal store and then linked into each
agent's own skills directory:

| Scope   | Universal store          |
|---------|--------------------------|
| Global  | `~/.agents/skills/<skill>`   |
| Project | `./.agents/skills/<skill>`   |

- Agents that already read `~/.agents/skills` (Codex, OpenCode, Gemini CLI, Copilot,
  Amp, Warp, Zed, Cline) are covered by the store directly — no extra link.
- Agents with their own dir get a symlink (or copy) → the store:
  Claude Code (`~/.claude/skills`), Cursor (`~/.cursor/skills`), Hermes
  (`$HERMES_HOME/skills`), OpenClaw (`~/.openclaw/skills`), Windsurf, Continue,
  Goose, Devin, AiderDesk.

Because it's one source of truth, **updating once updates every agent** (symlink mode).

### Relocatable bundle

`make-pdf` leans on sibling support dirs (`scripts/`, `assets/templates/`,
`references/`). The installer assembles a self-contained bundle so the skill works
detached from the Claude plugin:

```text
~/.agents/skills/make-pdf/
├── SKILL.md
├── scripts/      (build.py, doctor.py, marp_prep.py, check_links.py, setup_profile.py)
├── assets/       (templates/ + shared SVG)
├── references/
└── examples/profile.example.yaml
```

`build.py` resolves its plugin root relative to its own location, so it runs
unchanged from here.

### What is and isn't portable

- **Portable:** reading `SKILL.md`, rendering via `build.py`, and the
  `setup_profile.py` profile wizard — anywhere with `python3` + the render toolchain.
- **Claude-Code-only (not shipped to other agents):** the background monitors
  (`monitors.json`), the `template-builder` parallel subagent fan-out, and
  `AskUserQuestion`-driven pickers. On other agents the skill degrades gracefully —
  it just runs `build.py` over bash and prompts inline.
- **Runtime toolchain** (checked by `scripts/doctor.py`): `pandoc`, `tectonic`,
  `@marp-team/marp-cli` (via `npx`), `rsvg-convert`, `poppler` (`pdfinfo`/`pdftotext`),
  headless Chrome, `python3` + PyYAML. The installer surfaces anything missing.

## Profile setup outside the installer

The same canonical writer can be run any time:

```text
python3 ~/.agents/skills/make-pdf/scripts/setup_profile.py            # interactive
python3 ~/.agents/skills/make-pdf/scripts/setup_profile.py --print-path
echo '[{"company":"Acme Corp","author":"Docs Team"}]' \
  | python3 ~/.agents/skills/make-pdf/scripts/setup_profile.py --json --mode overwrite
```

Honours `$DOCSMITH_HOME` (default `~/.docsmith`).
