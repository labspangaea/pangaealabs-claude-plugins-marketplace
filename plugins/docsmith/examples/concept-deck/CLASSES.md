# concept-deck — slides

`concept-deck` is **technical-doc, SVG-first**: each concept is one hand-written
full-canvas SVG (`<!-- _class: figure full -->`), and the slide chrome is deliberately
minimal. This example is [`rag-system-design.md`](rag-system-design.md) →
[`rag-system-design.pdf`](rag-system-design.pdf) (9 slides, 1440×810pt); PNG exports in
[`pages/`](pages/). The footer (mono) on every slide carries the **Pangaea Digital Labs**
logo + author + copyright (`--company "Pangaea Digital Labs"`).

The look: flat **near-white** field (`#F4F6FD`), heavy **Poppins black** titles, `// mono`
tech tags + mono footer, bold **black-outlined multi-pastel cards**, **black** orthogonal
connectors, flat **sticker icons**. Signal blue (`#3FA9F5`) is the only accent; the one
navy `statement` slide is the dark punctuation.

| # | Class | What it is |
| :--- | :--- | :--- |
| 1 | `cover` | Title — `// PANGAEA LABS · SYSTEM DESIGN`, Poppins-900 headline, intro line |
| 2 | `figure full` | **100%-SVG** — *RAG, end to end*, a **2×2 framed-panel composite** (doc→chunks · vector space · top-K scatter · merge-flow) (`diagrams/concept-overview.svg`) |
| 3 | `figure full` | **100%-SVG** — *Without RAG, it guesses* (`diagrams/concept-problem.svg`) |
| 4 | `figure full` | **100%-SVG** — *The RAG architecture*, 5-node loop (`diagrams/concept-architecture.svg`) |
| 5 | `figure full` | **100%-SVG** — *The RAG pipeline*, 4 numbered stages (`diagrams/concept-pipeline.svg`) |
| 6 | `figure full` | **100%-SVG** — the 12-icon sticker kit (`diagrams/icon-sheet.svg`) |
| 7 | `figure full` | **100%-SVG** — *The RAG lifecycle*, a **3-lane swim-lane pipeline** (ingest · serve · evaluate), numbered steps + cross-lane + feedback loop (`diagrams/concept-lifecycle.svg`) |
| 8 | `statement` | The one **navy** full-bleed slide — *Fine-tuning edits the brain. RAG edits the desk.* |
| 9 | `closing` | Centered sign-off |

**Slides 2–7 are each one full-canvas `1920×1080` SVG** — the signature concept-deck
pattern. Two composite styles are shown: a **quad-panel** poster (slide 2) and a
**swim-lane pipeline** (slide 7). A `figure full` SVG has no complexity ceiling. The diagrams live in [`diagrams/`](diagrams/); the generation spec (palette,
strokes, full-slide template, icon library, **big multi-panel patterns**, recipes) is in
[`../../assets/templates/concept-deck/icons.md`](../../assets/templates/concept-deck/icons.md).

**Class set** is minimal by design — `cover` · `figure`(+`full`/`bare`) · `statement` ·
`closing` · `cards` · code · callouts. The decorative deck classes (kpi/versus/scorecard/
flow/roadmap/…) are intentionally removed; the SVG is the content.
