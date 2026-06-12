# Release notes

Release history for the plugins in the **pangaealabs-claude-plugins-marketplace**.
New entries are added (newest first) by the `/release-pangaealabs-plugin`
maintainer command at release time — see `.claude/commands/release-pangaealabs-plugin.md`.

<!-- RELEASES:TOP — the release command inserts each new entry directly below this line, newest first -->

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
