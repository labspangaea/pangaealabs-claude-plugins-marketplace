# `handbook` design system

A polished LaTeX **book** (pandoc + tectonic), extracted from `ai-roadmap.pdf`.
6.5×9.25in trim, two-sided, Latin Modern serif body.

## Tokens
Colours live in `design-system.yaml` (flat names → LaTeX `\definecolor`). Primary
navy `#003060`; semantic callout colours amber/red/green/violet. Override per-doc
via front-matter `overrides.colors`, or globally via `~/.docsmith/template/handbook.yaml`.

## Type
- Body: Latin Modern Roman, ~11pt, justified, block paragraphs (parskip).
- Headings: Latin Modern Sans, navy, bold. Matter titles (Contents) serif-bold black.
- Code: Latin Modern Mono.

## Components (authored as fenced `:::` divs)
| Div class | Renders as |
|---|---|
| `::: anchor` / `::: note` | navy pill-tab card |
| `::: tip` | amber "Pro Tip" pill-tab card |
| `::: warning` | deep-amber "Watch Out" card |
| `::: do` / `::: dont` | green / red pill-tab cards |
| `::: plain` | violet "In Plain English" card |
| `::: cheatsheet` / `::: alert` | full-width red banner card |
| `::: pullquote` | large navy italic with left rule |

Chapter openers (big navy numeral + rule + sans title), dotted-leader TOC, and
running heads are automatic. Title page is generated from config (company,
title, subtitle, author, date, version).

## Diagrams
Inline ` ```d2 ` blocks (bare) render as centred figures. For a caption use the
pandoc attribute form: ` ```{.d2 caption="…"} `.

## Backend
`template.yaml` → `backend: pandoc-tectonic`. `build.py` generates `_tokens.tex`
from the merged tokens, then runs pandoc with `preamble.tex`, `titlepage.tex`,
`callouts.lua`, and the shared `diagram.lua`.
