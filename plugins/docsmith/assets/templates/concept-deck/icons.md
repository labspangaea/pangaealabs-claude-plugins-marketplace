# concept-deck — SVG-DNA generation guide (+ icon library)

concept-deck is a **technical-documentation, SVG-first** template — *not* a decorative
deck. Think system-design notes, architecture diagrams, how-it-works flows. The slide
chrome is deliberately plain (flat near-white field, mono tags, black ink); **the content
is the hand-written SVG.** A slide is usually **one full-canvas SVG**
(`<!-- _class: figure full -->`). Read this whole file before generating a diagram.

---

## 1 · The DNA (reproduce this exactly)

| Element | Spec |
|---|---|
| **Ground** | Flat. Transparent (the field shows through) or a `#F4F6FD` rect. **No gradients, no shadows.** |
| **Title** | Top-center, **Poppins 900**, `#0A0A0A`, 1–2 lines, ~110–130px. |
| **Nodes** | Rounded-rect cards, `rx≈28`, **flat pastel fill**, **`stroke="#0A0A0A" stroke-width="4"`**. |
| **Pastel set** | mint `#A9F5D9` · peach `#FFDEB6` · pink `#F5A9C2` · blue `#BCD8FF` · lilac `#D8C8F5` |
| **Card text** | Label **Poppins 800 `#0A0A0A`** (no chip); body black. Icon left, label right. |
| **Doc motif** | "content" = horizontal rounded lines in a **darker tint** of the card (peach→`#E0975F`, pink→`#EA799E`, blue→`#8FB7F0`, mint→`#6FD9B0`). |
| **Icons** | Sticker look — **black outline (~6)**, white/pastel fills, **signal `#3FA9F5` accent dots**. Library in §5. |
| **Connectors** | **Orthogonal** (right-angle only), **`stroke="#0A0A0A" stroke-width="9–10"`**, solid triangular heads (marker §3). |
| **Arrow labels** | **Poppins 700 `#0A0A0A`**, centered on/above the line. |
| **Accent** | signal `#3FA9F5` — icon nodes + small highlights only. Ink stays black. |

**Vibe:** high-contrast, flat, engineering study-notes. If it looks soft, glossy, or
gradient-y, it's wrong.

---

## 2 · Canvas & coordinate grammar

- Full-slide diagram: `viewBox="0 0 1920 1080"`, set `width="1920" height="1080"`. Title
  baseline ~`160`; diagram body lives in `y≈260…980`; keep `~120` margins L/R.
- Hero (non-full) diagram: any size; author the `<svg>` **~1500–1760 wide** so it fills,
  and set both `width`+`height` (a size-less `<img>` collapses to nothing on a deck).
- **Card grid:** size cards ~`300×150`; gap ~`160` horizontally, ~`180` vertically. Snap
  every x/y to a tidy grid so connectors stay axis-aligned.
- **Connector routing:** only horizontal/vertical segments. For a feedback loop, route the
  return leg **below** all cards (`M<x1> <yBottom> V<low> H<x2> V<topOfTarget>`) so it never
  crosses a card. Put the arrowhead on the segment that *enters* the target.

---

## 3 · Arrow marker (always include in `<defs>`)

```xml
<marker id="ar" markerWidth="26" markerHeight="26" refX="17" refY="13" orient="auto" markerUnits="userSpaceOnUse">
  <path d="M2,2 L24,13 L2,24 Z" fill="#0A0A0A"/>
</marker>
```
Use `marker-end="url(#ar)"` on every connector. `markerUnits="userSpaceOnUse"` keeps the
head a fixed size regardless of stroke width.

---

## 4 · Full-slide template (copy, then fill)

A complete `figure full` slide skeleton — replace the cards/labels/arrows:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080" font-family="Poppins, sans-serif">
  <defs><marker id="ar" markerWidth="26" markerHeight="26" refX="17" refY="13" orient="auto" markerUnits="userSpaceOnUse"><path d="M2,2 L24,13 L2,24 Z" fill="#0A0A0A"/></marker></defs>
  <rect width="1920" height="1080" fill="#F4F6FD"/>                                   <!-- flat ground -->
  <text x="960" y="150" text-anchor="middle" font-size="120" font-weight="900" fill="#0A0A0A">Write-Ahead Log</text>

  <!-- nodes: pastel fill + 4px black outline -->
  <rect x="140" y="430" width="320" height="160" rx="28" fill="#BCD8FF" stroke="#0A0A0A" stroke-width="4"/>
  <rect x="800" y="430" width="320" height="160" rx="28" fill="#A9F5D9" stroke="#0A0A0A" stroke-width="4"/>
  <rect x="1460" y="430" width="320" height="160" rx="28" fill="#F5A9C2" stroke="#0A0A0A" stroke-width="4"/>

  <!-- labels: black Poppins 800 -->
  <text x="300"  y="525" text-anchor="middle" font-size="42" font-weight="800" fill="#0A0A0A">Client</text>
  <text x="960"  y="525" text-anchor="middle" font-size="42" font-weight="800" fill="#0A0A0A">WAL</text>
  <text x="1620" y="525" text-anchor="middle" font-size="42" font-weight="800" fill="#0A0A0A">Table</text>

  <!-- connectors: black, orthogonal, labelled -->
  <path d="M460 510 H792"  fill="none" stroke="#0A0A0A" stroke-width="10" marker-end="url(#ar)"/>
  <path d="M1120 510 H1452" fill="none" stroke="#0A0A0A" stroke-width="10" marker-end="url(#ar)"/>
  <text x="626"  y="485" text-anchor="middle" font-size="26" font-weight="700" fill="#0A0A0A">append</text>
  <text x="1286" y="485" text-anchor="middle" font-size="26" font-weight="700" fill="#0A0A0A">flush</text>
</svg>
```

Embed (no pandoc `{width=}` — marp leaks it):

```
<!-- _class: figure full -->

![Write-ahead log](/abs/path/diagrams/wal.svg)
```

---

## 5 · Icon library — each a `<g>` in a `0..120` box

Wrap to place: `<g transform="translate(X,Y) scale(s)">…icon…</g>` — usually the left of a
card (`translate(cardX+24, cardY+18) scale(0.8)`), label to its right.

**User** — person + ? bubble
```xml
<g stroke="#0A0A0A" stroke-width="6">
  <circle cx="48" cy="44" r="22" fill="#fff"/>
  <path d="M20 100 C20 70 76 70 76 100 Z" fill="#fff"/>
  <rect x="74" y="20" width="40" height="30" rx="8" fill="#fff"/>
  <text x="94" y="43" font-size="22" font-weight="900" fill="#0A0A0A" text-anchor="middle" stroke="none">?</text>
</g>
```

**LLM / brain** — white brain, signal nodes
```xml
<g transform="translate(-196,-148) scale(0.77)">
  <path d="M270 286 C258 252 286 218 318 226 C330 204 360 204 372 226 C406 220 430 252 414 284 C428 306 406 332 374 326 C362 344 320 344 310 326 C280 330 256 308 270 286 Z" fill="#fff" stroke="#0A0A0A" stroke-width="6"/>
  <path d="M342 224 C350 252 334 270 344 294 C352 312 340 322 342 330" fill="none" stroke="#0A0A0A" stroke-width="4" stroke-linecap="round"/>
  <g fill="#3FA9F5"><circle cx="300" cy="252" r="7"/><circle cx="332" cy="238" r="7"/><circle cx="362" cy="252" r="7"/><circle cx="316" cy="296" r="7"/><circle cx="356" cy="296" r="7"/></g>
</g>
```

**Search** — magnifier
```xml
<g fill="none" stroke="#0A0A0A" stroke-width="7" stroke-linecap="round">
  <circle cx="52" cy="50" r="30" fill="#E8FBF2"/>
  <line x1="74" y1="72" x2="100" y2="98" stroke-width="14"/>
  <line x1="40" y1="44" x2="66" y2="44" stroke="#3FA9F5" stroke-width="6"/>
  <line x1="40" y1="56" x2="60" y2="56" stroke="#3FA9F5" stroke-width="6"/>
</g>
```

**Database** — cylinder
```xml
<g fill="#fff" stroke="#0A0A0A" stroke-width="6">
  <path d="M28 32 V88 a32 14 0 0 0 64 0 V32 Z"/>
  <ellipse cx="60" cy="32" rx="32" ry="14"/>
  <path d="M28 56 a32 14 0 0 0 64 0" fill="none"/>
  <path d="M28 78 a32 14 0 0 0 64 0" fill="none"/>
  <ellipse cx="60" cy="32" rx="32" ry="14" fill="none" stroke="#3FA9F5" stroke-width="4"/>
</g>
```

**Document** — file + signal lines
```xml
<g stroke="#0A0A0A" stroke-width="6" stroke-linejoin="round">
  <path d="M34 16 H78 L96 36 V104 H34 Z" fill="#fff"/>
  <path d="M78 16 V36 H96" fill="none"/>
  <g stroke="#3FA9F5" stroke-width="5" stroke-linecap="round"><line x1="46" y1="56" x2="84" y2="56"/><line x1="46" y1="70" x2="84" y2="70"/><line x1="46" y1="84" x2="72" y2="84"/></g>
</g>
```

**Process / gear** — cog with signal hub
```xml
<g stroke="#0A0A0A" stroke-width="5" stroke-linejoin="round">
  <g fill="#fff">
    <rect x="52" y="12" width="16" height="22" rx="3"/><rect x="52" y="86" width="16" height="22" rx="3"/>
    <rect x="12" y="52" width="22" height="16" rx="3"/><rect x="86" y="52" width="22" height="16" rx="3"/>
    <rect x="22" y="22" width="18" height="18" rx="3" transform="rotate(45 31 31)"/>
    <rect x="80" y="22" width="18" height="18" rx="3" transform="rotate(45 89 31)"/>
    <rect x="22" y="80" width="18" height="18" rx="3" transform="rotate(45 31 89)"/>
    <rect x="80" y="80" width="18" height="18" rx="3" transform="rotate(45 89 89)"/>
  </g>
  <circle cx="60" cy="60" r="30" fill="#fff"/>
  <circle cx="60" cy="60" r="13" fill="#3FA9F5"/>
</g>
```

**Cache** — lightning bolt
```xml
<g stroke="#0A0A0A" stroke-width="6" stroke-linejoin="round"><path d="M66 12 L32 66 H56 L50 108 L88 50 H62 Z" fill="#3FA9F5"/></g>
```

**Queue** — stacked messages
```xml
<g stroke="#0A0A0A" stroke-width="6">
  <rect x="20" y="34" width="80" height="16" rx="8" fill="#fff"/>
  <rect x="20" y="58" width="80" height="16" rx="8" fill="#fff"/>
  <rect x="20" y="82" width="80" height="16" rx="8" fill="#fff"/>
  <g fill="#3FA9F5" stroke="none"><circle cx="33" cy="42" r="3.5"/><circle cx="33" cy="66" r="3.5"/><circle cx="33" cy="90" r="3.5"/></g>
</g>
```

**API / cloud**
```xml
<g stroke="#0A0A0A" stroke-width="6" stroke-linejoin="round"><path d="M38 92 C20 92 18 66 38 62 C38 40 74 38 76 60 C98 56 102 92 80 92 Z" fill="#fff"/></g>
```

**Embeddings** — bordered signal dot-grid
```xml
<g>
  <rect x="18" y="18" width="84" height="84" rx="12" fill="#fff" stroke="#0A0A0A" stroke-width="5"/>
  <g fill="#3FA9F5"><circle cx="38" cy="38" r="7"/><circle cx="60" cy="38" r="7"/><circle cx="82" cy="38" r="7"/><circle cx="38" cy="60" r="7"/><circle cx="60" cy="60" r="7"/><circle cx="82" cy="60" r="7"/><circle cx="38" cy="82" r="7"/><circle cx="60" cy="82" r="7"/><circle cx="82" cy="82" r="7"/></g>
</g>
```

**Auth / lock**
```xml
<g stroke="#0A0A0A" stroke-width="6" stroke-linejoin="round">
  <rect x="28" y="50" width="64" height="54" rx="10" fill="#fff"/>
  <path d="M40 50 V38 a20 20 0 0 1 40 0 V50" fill="none"/>
  <circle cx="60" cy="74" r="7" fill="#3FA9F5"/>
</g>
```

**Verdict** — check badge (swap path to an `M44 46 L76 78 M76 46 L44 78` for a reject ✗)
```xml
<g stroke="#0A0A0A" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">
  <circle cx="60" cy="60" r="40" fill="#fff"/>
  <path d="M42 62 L56 76 L82 46" fill="none"/>
</g>
```

---

## 6 · Diagram recipes

- **Linear pipeline** — cards in a row, `H` arrows between: `A → B → C`. Label each arrow.
- **Feedback loop** — linear row + one return connector routed **below** the cards back to the start.
- **Hub-and-spoke** — one centre card, arrows radiating to satellites.
- **Layered stack** — rows = tiers (client / service / data), vertical arrows between rows.

Worked examples: [`examples/concept-deck/diagrams/rag-architecture.svg`](../../../examples/concept-deck/diagrams/rag-architecture.svg) (loop) ·
[`icon-sheet.svg`](../../../examples/concept-deck/diagrams/icon-sheet.svg) (all icons).

---

## 7 · Big / multi-panel diagrams (course-grade)

A `figure full` SVG has **no complexity ceiling** — a dense composite renders the same as
a 3-box flow. Don't default to a tiny diagram; if the concept has parts, draw them all.
Two structural patterns scale up:

**(a) Framed sub-panel grid** (a multi-topic poster). 2×2 or 2×3 rounded-rect panels, each
with a "legend tab" title that breaks the top border:
```xml
<g transform="translate(80,200)">
  <rect x="0" y="0" width="840" height="400" rx="24" fill="#fff" stroke="#0A0A0A" stroke-width="4"/>
  <rect x="200" y="-22" width="440" height="44" fill="#F4F6FD"/>   <!-- break border; WIDER than the title -->
  <text x="420" y="8" text-anchor="middle" font-size="40" font-weight="900" fill="#0A0A0A">Panel title</text>
  <!-- panel content in local 0..840 / 0..400 coords -->
</g>
```
Repeat at `(1000,200) (80,650) (1000,650)` for a 2×2 on a 1920×1080 canvas. **The gap rect
must be wider than the rendered title** or the panel border strikes through the text.

**(b) Swim-lane pipeline** (a CI/CD-style flow). Stacked lanes, each a rounded rect with a
left label-tab; numbered step badges + icons along the lane; curved dashed connectors:
```xml
<rect x="60" y="260" width="1800" height="240" rx="20" fill="#fff" stroke="#0A0A0A" stroke-width="4"/>
<rect x="60" y="260" width="240" height="240" rx="20" fill="#A9F5D9" stroke="#0A0A0A" stroke-width="4"/>
<text x="180" y="392" text-anchor="middle" font-size="38" font-weight="800" fill="#0A0A0A">Plan</text>
<circle cx="520" cy="320" r="26" fill="#3FA9F5" stroke="#0A0A0A" stroke-width="4"/>
<text x="520" y="331" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="28" fill="#04121f">1</text>
<path d="M560 360 C660 420 820 420 900 360" fill="none" stroke="#0A0A0A" stroke-width="6" stroke-dasharray="2 11" stroke-linecap="round" marker-end="url(#ar)"/>
```

### Domain primitives (drop into a panel/lane)

- **Array + index row** — a row of `<text>` cells over a greyed index row. Highlight a
  "window" with a rounded pastel `<rect rx>` drawn *behind* the cells.
- **Bar chart** — a row of `<rect>` bars (varying heights) + base value labels; mark a range
  with a curly brace `<path>`.
- **Scatter / vector cloud** — a bordered box + grey `<circle>` corpus points; a signal point
  for the query; ring + dashed line the top-K hits (see panel 3 of the example).
- **Vector** — `[` … `]` `<text>` wrapping a row of signal `<circle>` dots.
- **Tree** — `<circle>` nodes + straight edges; colour left/right edges differently; a dashed
  arc `<path>` for a "compare" relation.
- **Grid / board** — `<rect>` cells in a checker tint; drop icons (crown, ✓, ✗) in cells; a
  prohibition badge = `<circle>` + diagonal `<line>` in `#F2576B`.
- **Curved dashed arrow** — `<path d="M.. C..">` + `stroke-dasharray="2 11"` + `marker-end`.

**Worked example:** [`examples/concept-deck/diagrams/concept-overview.svg`](../../../examples/concept-deck/diagrams/concept-overview.svg)
— a 2×2 framed-panel RAG composite (doc→chunks · vector space · top-K scatter · merge-flow).
Inspiration: ByteByteGo course cards (quad-panel and swim-lane composites) — concept-deck
can reproduce that density; the only cost is hand-authoring, not the format.

## 8 · Fidelity checklist (DO / DON'T)

**DO** — flat `#F4F6FD`/transparent ground · `4px` black card outlines · `9–10px` **black**
orthogonal connectors with the `#ar` marker · Poppins 900 black title · Poppins 800 black
labels · signal only on icon nodes · snap to a grid · `width`+`height` on the `<svg>` ·
validate with `rsvg-convert -f pdf -o /tmp/x.pdf file.svg`.

**DON'T** — gradients or drop-shadows · diagonal/curved connectors (orthogonal only) · thin
(<4px) outlines · light/grey text on the field (ink is `#0A0A0A`) · signal-blue as a fill
or arrow colour (ink is black; signal is an *accent*) · pandoc `{width=}` (use `![w:NN]` or
a `figure`/`figure full` slide) · emoji as icons (use the §5 kit).
