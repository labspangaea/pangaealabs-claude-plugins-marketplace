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

### Footer & shared-chrome gotchas (learned the hard way)
The `footer` (logo · company · author · copyright) and the page number
(`section::after`) are SHARED across every slide class, so a rule written for one
layout can quietly break the branding everywhere. Watch for:
- **Don't let hero/content-image rules hit the footer logo.** A broad
  `section.<class> img:not(.emoji) { float; width; margin }` ALSO matches the
  `<img>` marp injects into the footer — it outranks `footer img` and leaks its
  float/width/margins, so the footer shifts differently on each slide class. Pin
  the footer logo defensively: `footer img { margin:0 !important; float:none
  !important; width:auto !important; max-width:none !important }` (or scope the
  hero selector to the content area, not all descendant `img`s).
- **Keep the footer on every content slide.** Hiding it per class
  (`section.<class> footer { display:none }`, e.g. to let a full-bleed element own
  the bottom) drops the branding there. Reserve room with the section's
  `padding-bottom` instead, so the bottom element sits *above* the footer band.
- **Centered layouts overflow onto the footer.** A `justify-content:center` class
  (figure/cover/closing) with a tall hero + long title/caption spills its bottom
  edge over the footer. Reserve a `padding-bottom` band AND give heroes a capped
  definite height (`height: NNvh; width:auto`) so a size-less or portrait SVG can't
  balloon to full height.
- **The page number and footer live in different frames.** marp reserves a footer
  band and parks `section::after` above it, so matching `bottom` values does NOT
  align them — nudge the page number onto the footer baseline with a uniform
  `transform: translateY(...)` (post-layout, so it's slide-class agnostic).
- **Color the code tokens or code reads dead.** marp emits highlight.js spans
  (`<span class="hljs-string">`, `hljs-keyword`, …) but ships no colors — add
  `.hljs-*` rules or every fenced block renders monochrome.

(Build mechanics the harness already handles: `build.py` closes marp-cli's stdin
so it can't hang waiting on input when spawned from a subagent/detached shell, and
passes `--html` only when `template.yaml` sets `html: true` — required for
raw-HTML constructs like `<aside class="callout …">`.)

## A pandoc/LaTeX template (backend: pandoc-tectonic)
1. `template.yaml`:
   ```yaml
   description: "LaTeX book — <palette/vibe>. Best for <use case>."
   backend: pandoc-tectonic
   pandoc_args: [--top-level-division=chapter, --number-sections, -V, documentclass=book]
   header_includes: [preamble.tex, titlepage.tex]   # after generated _tokens.tex
   lua_filters: [callouts.lua]
   ```
2. `design-system.yaml` — flat color names map 1:1 to `\definecolor` names used
   by `preamble.tex`; `build.py` generates `_tokens.tex` (with `\usepackage{xcolor}`).
3. `assets/preamble.tex` — structure/styling that consumes the token colours
   (do NOT hardcode hexes). `assets/titlepage.tex` defines `\dscover`.

## Then
- The new template appears automatically in the make-pdf multiSelect.
- Add a one-line entry to the plugin README and a `design-system.md` spec (give it
  a short **Diagrams** note: hand-written raw SVG embedded as a markdown image; no
  d2/Mermaid/image-gen).
- Verify: `python3 scripts/build.py --in evals/sample/<fixture>.md --out /tmp/x.pdf --template <name>`.
