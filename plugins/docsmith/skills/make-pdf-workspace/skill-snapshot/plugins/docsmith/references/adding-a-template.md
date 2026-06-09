# Adding a docsmith template

Every template is a folder under `assets/templates/<name>/` with the same
contract, overridable by `~/.docsmith/template/<name>.yaml`:

```
assets/templates/<name>/
  template.yaml           # manifest (backend + backend-specific bits)
  design-system.(yaml|css)# DEFAULT tokens as data
  design-system.md        # human-readable spec
  assets/                 # backend assets (preamble/theme/fonts/logos)
```

Every `template.yaml` should carry a one-line **`description:`** — a plain-language
summary of the look (palette, fonts, vibe, best use). `make-pdf` shows it beside the
name in the template chooser, so users pick by style, not just by name.

## A marp deck template (backend: marp-cli)
1. `template.yaml`:
   ```yaml
   description: "16:9 slides — <palette/fonts>, <vibe>. Best for <use case>."
   backend: marp-cli
   theme_name: docsmith-<name>
   theme_files: [theme.css]      # relative to assets/
   ```
2. `design-system.css` — a `:root { --token: value; }` block (and optional
   `@font-face` / Google-Fonts `@import`). This is the tokens layer.
3. `assets/theme.css` — the marp theme: style `section` (set `width:1920px;
   height:1080px` for 1440×810pt), `h6` (eyebrow), `h1`/`h2` (+ `em` accent),
   lists, `footer`, and one rule-set per `section.<class>` you support. Reuse the
   shared deck class vocabulary so existing sources render.
   Tip: use the `frontend-design` skill to craft a distinctive, non-generic theme.
4. Bundle fonts under `assets/fonts/` (relative `url(...)` paths are absolutized
   at build time) or `@import` them from Google Fonts.

## A pandoc/LaTeX template (backend: pandoc-tectonic)
1. `template.yaml`:
   ```yaml
   description: "LaTeX book — <palette/vibe>. Best for <use case>."
   backend: pandoc-tectonic
   pandoc_args: [--top-level-division=chapter, --number-sections, -V, documentclass=book]
   header_includes: [preamble.tex, titlepage.tex]   # after generated _tokens.tex
   lua_filters: [callouts.lua]                        # diagram.lua is auto-added
   ```
2. `design-system.yaml` — flat color names map 1:1 to `\definecolor` names used
   by `preamble.tex`; `build.py` generates `_tokens.tex` (with `\usepackage{xcolor}`).
3. `assets/preamble.tex` — structure/styling that consumes the token colours
   (do NOT hardcode hexes). `assets/titlepage.tex` defines `\dscover`.

## Then
- The new template appears automatically in the make-pdf multiSelect.
- Add a one-line entry to the plugin README and a `design-system.md` spec.
- Verify: `python3 scripts/build.py --in evals/sample/<fixture>.md --out /tmp/x.pdf --template <name> --diagrams-manifest /tmp/d.json`.
