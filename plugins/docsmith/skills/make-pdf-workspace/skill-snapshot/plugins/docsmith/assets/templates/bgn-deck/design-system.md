# `bgn-deck` design system

16:9 slides (marp-cli) for **Badan Gizi Nasional**. Tokens, fonts and logos are
**copied verbatim** from `~/Documents/BGN Design System/` (`colors_and_type.css`
→ `design-system.css`). Source of truth = that package; do not reinvent values.

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
people · versus · timeline · logowall · quote · statement (dark) · closing`.
Card-grid classes turn a markdown list into cards — each `- **value** text`
becomes a card with an emphasised value. `split` floats a diagram/image beside
the content. `versus` styles the first card as "before" (red) and the last as
"after" (green/gold).

## Diagrams
Inline ` ```d2 ` blocks render to SVG once (shared) and are injected as images.

## Backend
`template.yaml` → `backend: marp-cli`, `theme_name: docsmith-bgn-deck`,
`theme_files: [theme.css]`. `build.py` composes `design-system.css` + `theme.css`
(+ overrides) into one marp theme and renders at 1920×1080px (= 1440×810pt).
Override tokens per-doc via front-matter `overrides.tokens`, or globally via
`~/.docsmith/template/bgn-deck.yaml`.
