# `claudecode-deck` design system

16:9 slides (marp-cli), reconstructed from the "Claude for Everyone" deck — a
warm, editorial Anthropic/Claude style. No upstream asset package; tokens and
theme are authored here. Fonts via Google Fonts (OFL).

## Palette
Cream `#F0EEE6` page · surface `#F7F6EF` · **clay `#B85838`** (accent) · clay-soft
`#D8896B` · peach `#F5E6DA` (highlight) · ink `#262620` · ink-2 `#54514A` ·
hairline `#E2E0D6` · espresso `#262218` (dark slides).

## Type
Display/headlines = **Instrument Serif** (with clay *italic* accents); body =
**Manrope**; eyebrows/footer/page-no/code = **JetBrains Mono**.

## Authoring (marp)
- `###### EYEBROW` → clay dot + mono tracked-caps eyebrow.
- `# Headline with *accent*` → Instrument Serif; `*accent*` becomes clay italic.
- `<!-- _class: NAME -->` per slide.

## Slide classes
Shares the deck vocabulary so a source written for any deck renders here:
`cover · bigstat · kpi · pillars · cards3 · agenda · compare2 · compare3 ·
glossary · models · filegrid · featurepair · split · steps · people · versus ·
quote · statement (dark) · closing`. Card-grid classes turn a markdown list into
hairline cards; one card per group is peach-highlighted.

This theme adds four of its own:

- `stack` — top/bottom: heading, then a large **centered** figure, then an optional
  caption or `> callout`. Use when a wide diagram (timeline, flow, roadmap) reads
  better full-width than squeezed into a `split` side column.
- `iconcards` — each list item becomes a card with a small SVG icon pinned left and
  the title+desc stacked beside it. Author as
  `- ![](/abs/ic-x.svg) **Title** description`. 3-up by default; add `cols2` for 2-up.
- `procon` — a two-card pair tinted success-green (first) / error-red (last), for
  when the contrast (pros vs cons, do vs don't) IS the point.
- A `> line` on any **non-`quote`** slide renders as a clay-spined peach callout pill
  — lift a takeaway out of the body without spending a whole quote slide.

The footer is auto-composed by `build.py` from `logo · company · author · copyright`
and pinned to the same bottom band as the page number so they share one line; the
`author` is overridable per-document in front-matter.

## Diagrams, charts & icons
Author **hand-written raw SVG** (no d2/Mermaid/image-gen) and embed it as a markdown
image with an ABSOLUTE path: `![Caption](/abs/diagrams/flow.svg)`. Marp embeds the
SVG via Chrome — no pre-render step. Validate with `rsvg-convert` first, and give
every SVG an explicit `width`+`height` (not just a `viewBox`) — Chrome collapses a
size-less `<img>` to nothing. Small UI icons for `iconcards` are the same flow at
~64×64 (clay stroke, transparent ground).

**No white backgrounds.** Figures on `split`/`stack` slides sit directly on the
cream wash — there is no white card behind them — so author each SVG with a
**transparent** ground (use the cream/surface/peach tokens for fills, not `#fff`)
and rely on ink/clay strokes for definition. A white panel reads as a pasted
foreign asset against this warm editorial page. (Figure styles are also scoped to
**content** images — `section.split p img`, `section.iconcards li img` — so the
footer logo `<img>` is never restyled.)

## Backend
`backend: marp-cli`, `theme_name: docsmith-claudecode-deck`. Renders at
1920×1080px (= 1440×810pt). Override via front-matter `overrides.tokens` or
`~/.docsmith/template/claudecode-deck.yaml`.
