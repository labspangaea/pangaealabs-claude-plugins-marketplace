# Release notes

Release history for the plugins in the **pangaealabs-claude-plugins-marketplace**.
New entries are added (newest first) by the `/release-pangaealabs-plugin`
maintainer command at release time — see `.claude/commands/release-pangaealabs-plugin.md`.

<!-- RELEASES:TOP — the release command inserts each new entry directly below this line, newest first -->

## testcraft 0.1.0 — 2026-06-24
Add testcraft: user flows → test cases → offline console.
- Initial release. Two chained skills — `userflow-to-testcases` (author cases from a flow doc by
  modeling actor+resource state machines: per-transition cases with downstream impact, matrix,
  E2E journeys, VAPT pass) and `testcase-importer` (normalize any case data → canonical CSV →
  single-file offline HTML console).
- Two subagents: `testcase-architect`, `testcase-vapt-auditor`.
- Installer: added `-s/--skill` so multi-skill plugins install non-interactively; documented the
  skill-local support-dir layout alongside docsmith's plugin-level one.

## docsmith 0.9.4 — 2026-06-13
- **handbook: no more blank chapter-opener pages.** The template shipped the LaTeX
  `book` class with `twoside`+`openright`, which insert a blank verso before every
  chapter (to force it onto a right-hand page of a physical spread) plus a trailing
  blank — read on screen those are just "empty pages" (a demo carried 3 of them).
  The handbook now builds **digital-first** (`oneside`+`openany`): each chapter
  opens on the next available page, no blanks (the 14-page demo drops to 11). A doc
  headed for print-and-bind can opt back in with
  `overrides.classoptions: [twoside, openright]`.
- **Retired `strip_blank_pages.py`.** It was a post-build band-aid `make-pdf` ran as
  Step 7 to delete the filler pages — but it rebuilt the PDF without the `/Outlines`
  tree, silently destroying the **bookmarks added in 0.9.3** (verified: outline
  `True → False`). With the blanks gone at the source there is nothing to strip, so
  the script + its Step-7 call (in `make-pdf` SKILL.md and the authoring guide) are
  removed and the bookmarks survive intact.

## docsmith 0.9.3 — 2026-06-13
- **handbook polish** (from an `/impeccable critique`): the title page now groups the whole
  identity block at the optical centre (was author/date jammed to the bottom edge with a dead
  band above); the auto cover date is book-style "June 2026" (not ISO — a shared `build.py`
  change that improves every template's cover; explicit front-matter dates pass through
  unchanged); the fenced code block uses a full thin navy border instead of a left-rule
  side-stripe; and the rendered PDF now carries a **bookmark/outline** for navigation (a
  screen-reader / reader-wayfinding aid). Per-figure alt text + full PDF tagging remain a
  LaTeX/tectonic limitation (deferred).

## docsmith 0.9.2 — 2026-06-13
- **claudecode-deck accessibility** — the clay accent `#B85838` was normal-size on the
  eyebrow + page number at 4.03:1 on cream → added `--cc-clay-deep #9A4528` (**5.55:1**) for
  those uses (bright clay stays for large `*em*` + headlines); the `>` callout's 6px
  side-stripe became a full clay border.
- **handbook accessibility** — hyperlinks (`linkblue`) were 3.87:1 on white → `#1565C0`
  (**5.75:1**); secondary text (`rulegrey` captions / running head / footer / page number)
  3.45:1 → `#6B6B6B` (**5.33:1**); the Pro Tip callout title was white-on-amber 2.85:1 → a
  dark title on the bright amber tab (**7.38:1**).
- With this, **all five templates meet WCAG-AA contrast.**

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
