# concept-deck — design system

A **technical-documentation, SVG-first** template in the **ByteByteGo "concept card"**
idiom: a flat **near-white field**, bold **black-outlined multi-pastel cards**, **black
orthogonal connectors**, heavy **Poppins** black titles, flat **sticker icons**. 16:9 marp
deck (`1920×1080px → 1440×810pt`).

This is **not** a decorative deck like `kawaii-storybook`, nor a formal one like
`corporate-deck`. It's an engineering-reference shell: the chrome is deliberately plain
(flat field, mono `// tags`, mono footer, black ink) so the **hand-written SVG diagram is
the slide.** The intended pattern is **one full-canvas SVG per concept**
(`<!-- _class: figure full -->`); the CSS slide classes are a fallback for prose.

Pangaea identity is just the **electric-blue signal accent** (`#3FA9F5` — `// eyebrow`
tags, *em* words, page number, icon nodes) and the single **navy `statement`** slide.

> ### ► The SVG-DNA generation guide is the heart of this template
> Before authoring **any** diagram, read **[`icons.md`](icons.md)** — the precise SVG-DNA
> spec (canvas grammar, exact palette/strokes, a fill-in full-slide template, the 12-icon
> library, diagram recipes, and a fidelity DO/DON'T checklist). Generating faithful
> ByteByteGo SVG is the main job on this template.

> **Brand note.** Pangaea's brand is strictly two hues (navy + signal). concept-deck
> **intentionally departs** by using ByteByteGo's mint/peach/pink/blue card set — chosen
> for diagram legibility. Field, accent, ink, and the statement slide stay on-brand; only
> the card fills add hue.

## Palette (tokens in `design-system.css`)

| Token | Hex | Role |
|---|---|---|
| `--cd-field` | `#F4F6FD` | slide field (near-white, whisper of periwinkle) |
| `--cd-surface` | `#FFFFFF` | code cards · table · callouts |
| `--cd-ink` | `#0A0A0A` | **titles · card outlines · connectors · card text** |
| `--cd-ink-2` | `#2A3550` | body text on the field |
| `--cd-signal` | `#3FA9F5` | accent — eyebrow · *em* · page no · bullets · icon nodes |
| `--cd-void` | `#0A1A2F` | the one navy `statement` slide |
| `--cd-card-blue/mint/peach/pink/lilac` | `#BCD8FF` `#A9F5D9` `#FFDEB6` `#F5A9C2` `#D8C8F5` | card fills (cycled) |
| `--cd-line-peach/pink/...` | `#E0975F` `#EA799E` … | darker tints for the "document lines" motif |
| `--cd-bw` | `4px` | the signature bold black outline weight |

**Type:** Poppins (display 800/900 + body), JetBrains Mono (code) — both `@import`ed
(OFL). **Depth = bold black borders, not shadows** (blurred shadows render as hard grey
rectangles in many PDF viewers).

## Slide classes (deliberately minimal)

Trimmed to a tech-doc, SVG-first set — the decorative deck classes (kpi/pillars/versus/
scorecard/flow/roadmap/scenarios/path/laws/…) are **intentionally absent**; an unknown
`_class` just falls back to a plain content slide.

| Class | Use |
| :--- | :--- |
| **`figure full`** | **the primary class** — a 100%-SVG slide, edge-to-edge (no title/padding). One per concept. |
| `figure` / `figure bare` | a hand-written SVG hero, centered + capped (with/without rounded corners) |
| `cover` | title slide — `// mono eyebrow`, heavy black headline, intro line |
| `statement` | the one **navy** full-bleed slide (dark punctuation), white headline + signal accent |
| `closing` | centered sign-off |
| `cards` | the **only** prose layout — auto-fit grid, black-outlined pastel cards (`- **Title** body`) |
| *(default)* | headings + bullet lists + fenced **code** + `<aside class="callout …">` callouts |

Author: `###### EYEBROW`, `# Headline with *signal accent*`. Callouts:
`<aside class="callout tip|note|warning|plain|do|dont">` (blank line around inner content).
**The intended pattern is `figure full` — one hand-written SVG per concept.**

## Diagrams — hand-written raw SVG (the signature visual)

Embed by **absolute path** with explicit `width`+`height` on the `<svg>`:

```
![How RAG works](/abs/path/diagrams/rag.svg)
```

**Sizing is marp-native, not pandoc.** Do *not* use `{width=92%}` — marp leaks it as
text. A `figure`-class slide auto-fits the hero (fills ~94% width); a `figure full` slide
gives an SVG the whole `1920×1080` canvas (no title/padding). To size one image manually
use `![w:1500](/abs/diagrams/rag.svg)`; author the `<svg>` itself ~`1500–1760` wide.

Inside the diagram, on the near-white field:

- **Cards:** pastel fill + `stroke="#0A0A0A" stroke-width="4"`, `rx≈28`. Labels + body **black**.
- **Connectors:** orthogonal **black** arrows, `stroke="#0A0A0A" stroke-width="10"`, solid heads.
- **Field-level text** (title, arrow labels): **black** (`#0A0A0A`) — it sits on the light field.
- **Icons:** the [`icons.md`](icons.md) kit — black outlines, white/pastel fills, **signal** accent dots.
- **Document motif:** stored content as horizontal rounded lines in a darker tint of the card.
- **Ground:** transparent (the field shows through) or a `#F4F6FD` ground rect on a `full` slide.

Validate before embedding: `rsvg-convert -f pdf -o /tmp/x.pdf diagrams/x.svg`. The full
icon library, arrow marker, and diagram recipes (linear / loop / hub / layered /
whole-slide) live in **[`icons.md`](icons.md)**; worked examples in
[`examples/concept-deck/diagrams/`](../../../examples/concept-deck/diagrams/).

### Minimal example

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 320" width="1400" height="320" font-family="Poppins, sans-serif">
  <defs><marker id="ar" markerWidth="24" markerHeight="24" refX="16" refY="12" orient="auto" markerUnits="userSpaceOnUse"><path d="M2,2 L22,12 L2,22 Z" fill="#0A0A0A"/></marker></defs>
  <rect x="60"  y="100" width="320" height="120" rx="28" fill="#BCD8FF" stroke="#0A0A0A" stroke-width="4"/>
  <rect x="1020" y="100" width="320" height="120" rx="28" fill="#F5A9C2" stroke="#0A0A0A" stroke-width="4"/>
  <text x="220" y="172" text-anchor="middle" font-size="40" font-weight="800" fill="#0A0A0A">User</text>
  <text x="1180" y="172" text-anchor="middle" font-size="40" font-weight="800" fill="#0A0A0A">LLM</text>
  <path d="M388 160 H1012" fill="none" stroke="#0A0A0A" stroke-width="10" marker-end="url(#ar)"/>
  <text x="700" y="138" text-anchor="middle" font-size="26" font-weight="700" fill="#0A0A0A">augmented prompt</text>
</svg>
```
