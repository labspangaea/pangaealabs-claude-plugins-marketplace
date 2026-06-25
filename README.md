# Pangaea Labs — Claude Code Plugins Marketplace

A [Claude Code](https://claude.com/claude-code) plugin marketplace by
**[Pangaea Digital Labs](https://www.pangaea.id/)**. Add it once, then install any plugin below.

## Add the marketplace

```bash
# from the Claude Code REPL
/plugin marketplace add labspangaea/pangaealabs-claude-plugins-marketplace
```

Prefer another agent? An interactive `npx` installer puts these skills into **any** agent
(Claude Code, OpenClaw, Hermes, Cursor, Codex, OpenCode, Gemini CLI, Copilot, Warp, Zed, …):

```bash
npx github:labspangaea/pangaealabs-claude-plugins-marketplace
```

See **[docs/install.md](docs/install.md)** for the cross-agent flow, flags, and portability model.

## Plugins

### `docsmith` — markdown → professional, on-brand PDFs

<img src="plugins/docsmith/examples/corporate-deck/pages/page-01.png" width="640" alt="A docsmith-rendered corporate-deck cover slide — one of five on-brand PDF templates.">

Turn markdown into polished, on-brand PDFs across **5 design-system templates** — a LaTeX
`handbook` plus four 16:9 deck styles (`corporate-deck`, `claudecode-deck`, `kawaii-storybook`,
`concept-deck`). `/make-pdf` picks one template and one company brand per run; every diagram,
chart, and icon is hand-written raw SVG embedded inline (no d2, Mermaid, or image generation).

```bash
/plugin install docsmith@pangaealabs-claude-plugins-marketplace
```

▸ **Templates, the full rendered gallery, config & profile setup → [docsmith README](plugins/docsmith/README.md)**

### `testcraft` — user flows → test cases → offline console

<img src="plugins/testcraft/assets/console-preview.png" width="640" alt="The testcase-importer console — a single-file offline test matrix with severity-colored rows, faceted filters (section / outcome / severity / type), and a legend.">

Turn an app's **user flows** into a complete, importer-ready **test-case suite** and a single-file,
offline **HTML console**. Two chained skills — `/userflow-to-testcases` authors cases from a flow
doc (state machines → per-transition cases with downstream impact → matrix → E2E → VAPT), and
`/testcase-importer` normalizes any case data and renders the console — plus two subagents
(`testcase-architect`, `testcase-vapt-auditor`) for the heavy authoring and the security pass.

```bash
/plugin install testcraft@pangaealabs-claude-plugins-marketplace
```

▸ **The pipeline, canonical schema & bundled scripts → [testcraft README](plugins/testcraft/README.md)**

---

_Maintaining a plugin in this repo? See **[CLAUDE.md](CLAUDE.md)** (monitors, evals, the release
command, and the optimizer gotchas)._

## License

© [Pangaea Digital Labs](https://www.pangaea.id/) — [www.pangaea.id](https://www.pangaea.id/)
