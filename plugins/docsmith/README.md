# docsmith

Turn markdown into professional, on-brand PDFs across **design-system templates**.
One source can fan out to several templates at once. Diagrams and art are
**hand-written raw SVG** embedded as markdown images (no d2/Mermaid/image-gen) —
the handbook converts them to PDF via rsvg-convert, the decks embed them via
Chrome. **PDF only.**

## Templates
| Template | Backend | Look |
|---|---|---|
| `handbook` | pandoc + tectonic | LaTeX **book** (6.5×9.25in), navy palette, callout cards, dotted-leader TOC. From `ai-roadmap.pdf`. |
| `bgn-deck` | marp-cli | 16:9 **slides**, Badan Gizi Nasional brand (navy/green/gold, BGN Sans + Lora). Assets copied from the BGN Design System. |
| `claudecode-deck` | marp-cli | 16:9 **slides**, Claude editorial (cream/clay, Instrument Serif + Manrope + JetBrains Mono). |
| `kawaii-storybook` | marp-cli | 16:9 **slides**, soft pastel storybook / NotebookLM (rotating washes, chip-cards, verdict pills, emoji + hand-drawn SVG heroes, full-bleed SVG scenes, callouts, code blocks; Baloo 2 + Nunito + Lora). From `The_Secure_Cloud_Village.pdf`. |

## Use it
Invoke the **`/docsmith:make-pdf`** skill (or just ask Claude to "make a PDF /
handbook / deck"). It checks tooling, asks which template to render, then builds
it (embedding any hand-written SVG diagrams/art directly).

Or run the scripts directly:
```bash
python3 scripts/doctor.py
python3 scripts/build.py --in DOC.md --out DOC.pdf --template bgn-deck
```

## Config (`~/.docsmith/`)
- `profile.yaml` — global identity/branding (author, company, logo, …).
- `template/<name>.yaml` — per-template token overrides.
- per-document front-matter `overrides:` — one-off tweaks.

## Requirements
`pandoc`, `tectonic`, `rsvg-convert` (SVG validation + handbook SVG→PDF),
`poppler` (pdfinfo/pdftotext), Node/`npx` (for marp-cli), and a headless Chrome.
Run `scripts/doctor.py`.

## Authoring & extending
See `references/authoring-guide.md` and `references/adding-a-template.md`. Each
template's design system is documented in `assets/templates/<name>/design-system.md`.
