# `kawaii-storybook` design system

16:9 slides (marp-cli), extracted from "The Secure Cloud Village" — a soft
pastel **storybook / NotebookLM** deck: per-slide pastel gradient washes, rounded
puffy cards, pastel **chip** labels, colour-coded **verdict pills**, and emoji
mascots. No upstream asset package; tokens and theme are authored here. Fonts via
Google Fonts (OFL).

## Palette
Per-slide gradient **washes** (cycled): butter `#FBF6E3` · mint `#DCEFE0` · rose
`#F8E0E4` · lavender `#E7E1F1` · sky `#DDEAF6` · peach `#FBE8DA`. Ink (headline)
`#3D3A37` · body `#4A4A4A` · soft `#7A746C` · **accent (clay)** `#C8623F`. Cards
white on hairline `#ECE7DC`. **Chips** (fill/text) blue · green · amber · pink ·
violet (cycled across cards). **Verdicts**: accept green `#7FCB86→#6BBE73`, reject
red `#E8604A→#D94A38`, caution amber `#F3D98A`. Sticky-note `#FBEF9E`.

## Type
Display/headlines = **Baloo 2** (rounded, super-bold) with clay `*accent*` words;
body = **Nunito**; quotes/closing italic = **Lora** italic; code = **JetBrains
Mono**. Soft "puffy" shadows + large card radius (28px) carry the storybook feel.

## Authoring (marp)
- `###### CHIP` → pastel rounded chip eyebrow.
- `# Headline with *accent*` → Baloo 2; `*accent*` becomes clay.
- `<!-- _class: NAME -->` per slide. Drop emoji (🐻🦊🦉🐹🐈‍⬛) inline as mascots —
  inside a heading they render large, doubling as "hero" stand-ins.
- Card-grid classes turn a markdown list into puffy cards; the `**bold**` lead of
  each card becomes a pastel chip (colour cycles per card).

## Slide classes
Shares the deck vocabulary so a source written for any deck renders here:
`cover · bigstat · kpi · pillars · cards · cards3 · agenda · compare2 · compare3 ·
split · steps · people · versus · timeline · quote · statement (dark) · closing`.

Signature additions:
- **`path`** (+ modifiers **`accept`** / **`reject`** / **`caution`**) — analysis
  layout: a floated hero (image or emoji) on the left, the list becomes stacked
  chip-cards (e.g. Concept / Appeal / Reality), and a `>` blockquote renders as the
  **verdict pill** (colour from the modifier, e.g. `<!-- _class: path reject -->`).
- **`laws`** — a 2×2 titled card grid.
- **`scorecard`** — a markdown table styled as a clipboard matrix (use emoji cells
  🟢🟡🔴) + a `>` blockquote conclusion bar.
- **`flow`** — a list → a row of numbered "stop" cards joined by connector chevrons.
- **`scenarios`** — rows of `**Stage** → **Action** → **Result**` (last row tints green).
- **`roadmap`** — zig-zag numbered signpost cards.
- **`figure`** — title + one large hero (author image **or** big emoji), centered.

A `>` blockquote on any slide renders as a soft conclusion/verdict pill.

## Backend
`backend: marp-cli`, `theme_name: docsmith-kawaii-storybook`. Renders at
1920×1080px (= 1440×810pt). Override via front-matter `overrides.tokens` or
`~/.docsmith/template/kawaii-storybook.yaml`.
