# Release notes

Release history for the plugins in the **pangaealabs-claude-plugins-marketplace**.
New entries are added (newest first) by the `/release-pangaealabs-plugin`
maintainer command at release time — see `.claude/commands/release-pangaealabs-plugin.md`.

<!-- RELEASES:TOP — the release command inserts each new entry directly below this line, newest first -->

## docsmith 0.9.1 — 2026-06-12
- **corporate-deck accessibility** — the gold page number on cream was 3.21:1 (below AA-normal)
  → deepened to gold-900 (**6.60:1**); the default list-bullet dot was bright green at 1.74:1
  (washed out) → green-700 (**3.45:1**); the `>` callout's 6px side-stripe became a full green
  border (+ the existing green-50 wash); and a broken token (`--bgn-green-600`, missing `var()`)
  was fixed. BGN brand identity preserved — all within the existing gold/green ramps.

## docsmith 0.9.0 — 2026-06-12
- **concept-deck SVG-template design system** — concept-deck's SVG authoring is now a
  reusable **two-mode** system in `icons.md`: **(A)** flat black-outlined pastel concept-card
  diagrams and **(B)** a new **isometric illustration** mode for covers + hero scenes
  (flat-shaded 3-tint cuboids — the ByteByteGo course-cover look, no gradients/shadows).
  Ships drop-in `svg-templates/` assets (`iso-cover.svg`, `iso-objects.svg`) + worked iso
  examples (`cover-rag.svg`, `vector-space.svg`); `make-pdf` now points authors at it.
- **concept-deck accessibility + contrast pass** — the electric-blue signal accent was
  illegible on the near-white field (2.37:1); text-on-field uses (eyebrow, *em*, links,
  page number) now use a deepened signal-ink (≥4.5:1), the code-syntax palette + captions
  clear WCAG AA, the side-stripe callout/code borders became full colour-coded borders, and
  off-token hexes are tokenised. The bright signal stays on the navy `statement` slide.

## docsmith 0.8.0 — 2026-06-12
- **New template: `concept-deck`** — a ByteByteGo-style, SVG-first technical-doc deck
  (flat near-white field, bold black-outlined multi-pastel cards, heavy Poppins titles,
  electric-blue signal accent). One full-canvas SVG per concept; author diagrams per its
  `icons.md` SVG-DNA guide.
- **kawaii-storybook accessibility + polish pass** — WCAG-AA contrast across the rendered
  PDF: accept verdict pills are now dark-ink-on-mint (were illegible white-on-green) and
  stay distinct from reject in grayscale / for colour-blindness; flow step badges legible;
  page number + soft ink deepened; the scorecard uses shape-distinct ✅/⚠️/❌ instead of
  hue-only dots. Removed the Comic Sans fallback; long content now wraps instead of
  overflowing the fixed canvas; dropped the side-stripe callout/code borders for full
  colour-coded borders.
- **`toolchain-doctor` monitor** — runs `scripts/doctor.py` at build start and tails
  `~/.docsmith/toolchain.log`, flagging a missing/broken toolchain (pandoc/tectonic/rsvg/
  marp/Chrome) — catches the environment failure class.

## docsmith 0.7.0 — 2026-06-10
- Handbook: uniform **light-blue** hyperlinks (TOC + cross-refs + URLs + citations)
  and a post-build link-integrity check (`scripts/check_links.py`) — internal gate
  plus an opt-in `--external` 404 probe.
- Examples regenerated as **full per-class catalogs** (every slide class / callout)
  for all four templates, each with a **footer logo** and a `CLASSES.md`; the
  made-up `profile.example.yaml` now carries logos (hand-written SVG → PNG).
- `make-pdf` builds **inline** by default (subagents only for multi-template fan-out).
- **Background monitor** (`monitors/monitors.json`) tails `~/.docsmith/render.log`;
  `build.py` logs one OK/FAIL line per render and captures the stderr tail on failure.
- kawaii-storybook: verdict-pill text vertically centered; image heroes are
  **transparent** (no white card / SVG ground panel). claudecode-deck: fixed the
  statement-slide footer logo (was whited-out by a brightness/invert filter).
- Maintainer commands: `/docsmith-render-triage` + `/docsmith-fix-loop` (the
  render-failure feedback loop) and `/release-pangaealabs-plugin`.

## docsmith 0.6.0 — 2026-06-10
Rename the `bgn-deck` template to `corporate-deck` (brand still comes from the
docsmith profile). Add runnable demos + a component gallery + a "how it works"
flow + a made-up `profile.yaml` example to the README, and document the
install/update commands.
