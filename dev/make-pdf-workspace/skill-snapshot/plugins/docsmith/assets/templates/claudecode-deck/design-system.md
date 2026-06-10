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

## Backend
`backend: marp-cli`, `theme_name: docsmith-claudecode-deck`. Renders at
1920×1080px (= 1440×810pt). Override via front-matter `overrides.tokens` or
`~/.docsmith/template/claudecode-deck.yaml`.
