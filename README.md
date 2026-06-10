# Pangaea Labs — Claude Code Plugins Marketplace

A [Claude Code](https://claude.com/claude-code) plugin marketplace by **Pangaea Labs**.
Add it once, then install any plugin below.

## Add the marketplace

```bash
# from the Claude Code REPL
/plugin marketplace add labspangaea/pangaealabs-claude-plugins-marketplace
```

## Plugins

### `docsmith` — markdown → professional, on-brand PDFs

Generate polished, on-brand PDFs from markdown using design-system templates.
The `/make-pdf` skill picks one template and one company brand per run and fans a
single source out to one or more PDFs via parallel subagents. Every visual —
diagram, chart, or illustration — is hand-written raw SVG embedded inline (no d2,
Mermaid, or image generation).

![How docsmith works: source.md + an optional ~/.docsmith/profile.yaml go through the /make-pdf skill and are rendered by marp-cli or pandoc+tectonic into an on-brand PDF.](plugins/docsmith/assets/how-it-works.svg)

**Templates**

- `handbook` — long-form report/guide as a LaTeX `book` (pandoc + tectonic)
- `corporate-deck` — 16:9 formal corporate / civic slides (marp-cli)
- `claudecode-deck` — 16:9 Claude/"claudecode"-branded slides (marp-cli)
- `kawaii-storybook` — 16:9 pastel storybook / NotebookLM-style deck (marp-cli)

Layered config lives under `~/.docsmith/` (global profile + per-template overrides
+ per-doc front-matter), so the plugin location is portable.

```bash
/plugin install docsmith@pangaealabs-claude-plugins-marketplace
```

Then, in any project:

```
/make-pdf turn report.md into a handbook PDF for Pangaea Labs
```

▸ **See every template's components rendered** — the flow diagram, a 4-template
gallery, and runnable demos with example prompts live in
**[the docsmith README](plugins/docsmith/README.md#gallery--every-templates-components-rendered)**
and **[`plugins/docsmith/examples/`](plugins/docsmith/examples/)**.

## License

© Pangaea Labs.
