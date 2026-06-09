# docsmith

Turn markdown into professional, on-brand PDFs across **design-system templates**.
One source can fan out to several templates at once; inline ` ```d2 ` diagrams
render once and are shared across every output. **PDF only.**

## Templates
| Template | Backend | Look |
|---|---|---|
| `handbook` | pandoc + tectonic | LaTeX **book** (6.5×9.25in), navy palette, callout cards, dotted-leader TOC. From `ai-roadmap.pdf`. |
| `bgn-deck` | marp-cli | 16:9 **slides**, Badan Gizi Nasional brand (navy/green/gold, BGN Sans + Lora). Assets copied from the BGN Design System. |
| `claudecode-deck` | marp-cli | 16:9 **slides**, Claude editorial (cream/clay, Instrument Serif + Manrope + JetBrains Mono). |
| `kawaii-storybook` | marp-cli | 16:9 **slides**, soft pastel storybook / NotebookLM (rotating washes, chip-cards, verdict pills, emoji mascots; Baloo 2 + Nunito + Lora). From `The_Secure_Cloud_Village.pdf`. |

## Use it
Invoke the **`/docsmith:make-pdf`** skill (or just ask Claude to "make a PDF /
handbook / deck"). It checks tooling, asks which template(s) to render, renders
shared diagrams once, then builds each template in parallel.

Or run the scripts directly:
```bash
python3 scripts/doctor.py
python3 scripts/render_diagrams.py --in DOC.md --cache ~/.docsmith/cache/diagrams --manifest /tmp/d.json
python3 scripts/build.py --in DOC.md --out DOC.pdf --template bgn-deck --diagrams-manifest /tmp/d.json
```

## Config (`~/.docsmith/`)
- `profile.yaml` — global identity/branding (author, company, logo, …).
- `template/<name>.yaml` — per-template token overrides.
- per-document front-matter `overrides:` — one-off tweaks.

## Requirements
`d2`, `pandoc`, `tectonic`, `rsvg-convert`, `poppler` (pdfinfo/pdftotext),
Node/`npx` (for marp-cli), and a headless Chrome. Run `scripts/doctor.py`.

## Authoring & extending
See `references/authoring-guide.md` and `references/adding-a-template.md`. Each
template's design system is documented in `assets/templates/<name>/design-system.md`.
