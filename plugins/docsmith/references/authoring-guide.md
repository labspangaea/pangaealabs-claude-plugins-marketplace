# docsmith authoring guide

One markdown source → professional PDFs across templates. This is the authoring
contract.

## Front-matter (per document)
```yaml
---
template: handbook            # default target; or  templates: [handbook, corporate-deck]
title: "My Document"
subtitle: "..."
date: auto                    # auto = today
version: "v1.0"
overrides:                    # optional, per-doc only
  colors: { navy: "#123456" } # handbook (LaTeX) token names
  tokens: { bgn-blue: "#123456" }  # deck (CSS) var names → :root override
---
```
Identity/branding (author, company, logo, …) comes from the global
`~/.docsmith/profile.yaml`; per-template defaults from
`assets/templates/<name>/`; per-template user overrides from
`~/.docsmith/template/<name>.yaml`. Merge order, later wins:
**template default → ~/.docsmith/template/<name>.yaml → profile → front-matter/overrides → CLI**.

## Diagrams (all templates)
Author **hand-written raw SVG** — plain XML using the primitives above (`<rect>`,
`<line>`, `<text>`, `<path>`, `<polygon>`, `<circle>`) with manual coordinates.
**No diagramming library, no Mermaid, no image generation.** Save each diagram as
a `.svg` file (e.g. in a `diagrams/` folder beside the doc) and embed it with a
markdown image using an ABSOLUTE path:
~~~
![My flow](/abs/path/diagrams/flow.svg){width=80%}
~~~
There is no pre-render step: the handbook (pandoc+tectonic) auto-converts SVG→PDF
via `rsvg-convert`, and decks (marp) embed the SVG via Chrome. The image alt text
becomes the figure caption. Absolute paths are required — the build runs from a
temp dir, so relative image paths won't resolve.

## handbook (LaTeX book)
- Chapters = `#`, sections = `##`. TOC, chapter openers, running heads, and the
  title page are automatic (title page from config).
- Callouts are fenced divs:
  - `::: tip` … `:::`  → amber "Pro Tip"
  - `::: note` / `::: anchor` → navy note
  - `::: warning` → "Watch Out"
  - `::: do` / `::: dont` → green / red
  - `::: plain` → "In Plain English"
  - `::: cheatsheet` → full-width red banner
  - `::: pullquote` → large navy italic
- Inline emphasis: `*italic*`, `**bold**`.
- Links/citations: write every source as `[label](url)`. All links — TOC,
  internal cross-refs, external URLs, citations — render in a uniform light blue
  (`linkblue #1565C0`) and stay clickable. Bare URLs do NOT auto-link —
  always wrap them. Put a blank line before any list (a tight bold-lead-in + list
  collapses into one paragraph).
- Long docs: close with a `## Glossary` (term/meaning table). After building, run
  `scripts/strip_blank_pages.py OUT.pdf` to drop the `book`-class filler pages.

## decks (corporate-deck, claudecode-deck, kawaii-storybook) — marp
- Separate slides with `---`.
- Pick a layout per slide with a marp directive: `<!-- _class: kpi -->`.
- Slide elements:
  - `###### EYEBROW` → the small tracked-caps label.
  - `# Headline with *accent*` → big headline; `*accent*` is the brand-accent italic.
  - paragraphs → body; `> quote` → quote slides.
  - lists → on card classes, each `- **value** text` becomes a card.
- Shared class vocabulary (works in either deck theme):
  `cover · bigstat · kpi · pillars · cards3 · agenda · compare2 · split ·
  steps · people · versus · quote · statement · closing`
  (claudecode-deck adds `compare3 · glossary · models · filegrid · featurepair`).
- `split` floats a diagram/image beside the content (put the SVG image first,
  then the text).
- `versus` styles the first card as "before" and the last as "after".

### kawaii-storybook extras
A soft pastel storybook theme. Beyond the shared vocabulary it adds:
- `path` — a hero (image or big emoji, placed first) on the left, then a list of
  chip-cards, then a `> verdict` pill. Tint the verdict with a modifier class:
  `<!-- _class: path accept -->` (green), `path reject` (red), `path caution` (amber).
- `laws` — a 2×2 titled card grid.
- `scorecard` — a markdown table → clipboard matrix (use shape-distinct cells ✅⚠️❌,
  not hue-only 🟢🟡🔴 — the dots are indistinguishable for colour-blind readers / in grayscale), plus
  a `> conclusion` bar.
- `flow` — a list → a row of numbered "stop" cards joined by connector chevrons.
- `scenarios` — a list of rows; write `**Stage** → **Action** → **Result**` (each
  `**bold**` becomes a pill; the last row tints green).
- `roadmap` — a list → zig-zag numbered signpost cards.
- `figure` — a centered title + one large hero (image **or** big emoji).
- Drop emoji 🐻🦊🦉🐹🐈‍⬛ inline as mascots; inside a heading they render large.
- A `> blockquote` on any slide renders as a soft conclusion/verdict pill.
- **SVG hero / character** — embed a hand-written raw SVG (same flow as handbook
  diagrams) as the hero of `path`/`figure`/`split`/`cover`:
  `![Bara](/abs/diagrams/hero.svg)`. It floats on a white card; add `bare`
  (`<!-- _class: figure bare -->`) to drop the card so the character sits on the wash.
  Give the SVG explicit `width`+`height` (not just a `viewBox`) — a size-less SVG
  embedded as an `<img>` collapses to nothing in Chrome.
- **SVG scene (full-bleed background)** — marp's background directive:
  `![bg cover](/abs/diagrams/scene.svg)`, `![bg right:40%](…)`, or
  `![bg opacity:.3](…)`. Overrides the per-slide pastel wash only where supplied.
- **Callouts** — `<aside class="callout tip">…</aside>` (HTML passthrough is on for
  kawaii). Variants mirror the handbook: `tip`/`note`/`anchor`/`warning`/`plain`/`do`/`dont`.
  Leave a **blank line around the inner content** so the markdown inside renders.
- **Code blocks** — fenced ```` ``` ```` blocks become a soft rounded card (full violet
  outline, mono); inline `` `code` `` stays an amber chip. Keep on-slide snippets short.

## Output
PDF only. Decks are 1440×810pt (16:9); the handbook is a 6.5×9.25in book.
Run via the `make-pdf` skill, or directly:
```
python3 scripts/build.py --in DOC.md --out DOC.pdf --template corporate-deck
```
