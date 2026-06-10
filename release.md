# Release notes

Release history for the plugins in the **pangaealabs-claude-plugins-marketplace**.
New entries are added (newest first) by the `/release-pangaealabs-plugin`
maintainer command at release time — see `.claude/commands/release-pangaealabs-plugin.md`.

<!-- RELEASES:TOP — the release command inserts each new entry directly below this line, newest first -->

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
