# `corporate-deck` design system

16:9 slides (marp-cli) for **formal corporate & civic decks**. The bundled default
tokens, fonts and logos are **copied verbatim** from a government design system
(`~/Documents/BGN Design System/`, `colors_and_type.css` → `design-system.css`) —
treat that package as the source of truth for the defaults; rebrand per company via
the docsmith profile rather than reinventing values.

## Palette
Brand blue `#071e49` · green `#92d05d` (eyebrow `#5a9438`) · sky `#b5e0ea` ·
gold `#d1b06c` · cream `#faf8f3`. Full shade ramps + warm-gray neutrals live in
`design-system.css`.

## Type
Sans = BGN Sans (bundled) → Plus Jakarta Sans; serif = Lora italic (accents/quotes);
mono = JetBrains Mono. Eyebrows are tracked uppercase green.

## Authoring (marp)
- `###### EYEBROW` → green tracked-caps eyebrow.
- `# Headline with *accent*` → navy ExtraBold; `*accent*` becomes Lora-italic green.
- Pick a layout per slide with `<!-- _class: NAME -->`.

## Slide classes
`cover · bigstat · kpi · pillars · cards3 · agenda · compare2 · split · steps ·
people · versus · timeline · logowall · quote · statement (dark) · closing`, plus
`stack · iconcards · procon`. Card-grid classes turn a markdown list into cards —
each `- **value** text` becomes a card with an emphasised value. `split` floats a
diagram/image beside the content. `versus` styles the first card as "before" (red)
and the last as "after" (green/gold).

The three shared with `claudecode-deck`:

- `stack` — top/bottom: heading, then a large **centered** figure, then an optional
  caption or `> callout`. Use for a wide diagram (timeline, flow, roadmap).
- `iconcards` — each item becomes a card with a small SVG icon pinned left, title +
  desc beside it: `- ![](/abs/ic-x.svg) **Title** description`. 3-up; `cols2` for 2-up.
- `procon` — a two-card pair tinted success-green (first) / danger-red (last).
- A `> line` on any **non-`quote`** slide renders as a green-bordered callout pill.

## Diagrams
Author **hand-written raw SVG** (no d2/Mermaid/image-gen) and embed it as a
markdown image with an ABSOLUTE path: `![Caption](/abs/diagrams/flow.svg)`. Marp
embeds the SVG via Chrome — no pre-render step. Validate with `rsvg-convert` first.

## Backend
`template.yaml` → `backend: marp-cli`, `theme_name: docsmith-corporate-deck`,
`theme_files: [theme.css]`. `build.py` composes `design-system.css` + `theme.css`
(+ overrides) into one marp theme and renders at 1920×1080px (= 1440×810pt).
Override tokens per-doc via front-matter `overrides.tokens`, or globally via
`~/.docsmith/template/corporate-deck.yaml`.
