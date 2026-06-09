---
name: make-pdf
description: Generate professional, on-brand PDFs from markdown using docsmith's design-system templates. Use this whenever the user wants to turn markdown / notes / a report / an outline into a polished PDF, make a "handbook" or "slide deck", render to the BGN (Badan Gizi Nasional) or Claude/"claudecode" brand, produce a "professional PDF / good-looking PDF", or make a cute / kawaii / pastel / storybook / NotebookLM-style deck. Picks one template and one company per run. Diagrams are hand-written raw SVG embedded as images (no d2, Mermaid, or image generation). Templates today: `handbook` (LaTeX book via pandoc+tectonic), `bgn-deck`, `claudecode-deck`, and `kawaii-storybook` (16:9 slides via marp-cli). Do NOT use for editing existing PDFs or for plain `pandoc file.md` with no styling need.
allowed-tools: [bash, read, write, edit, grep, glob, AskUserQuestion, Task]
model: sonnet
---

# docsmith — make a PDF

Turn a markdown source into a polished, on-brand PDF. Each run renders one
template branded as one company; hand-written raw SVG diagrams are embedded into
that output as images (no diagramming library).

`PLUGIN_DIR` below is this plugin's root (the folder containing `scripts/` and
`assets/`). Resolve it once at the start (the directory two levels up from this
SKILL.md).

## Always-apply quality checklist (document-style PDFs)

For long-form documents — anything built with the **handbook** template (reports,
guides, research, handbooks) — these seven checks are part of a finished PDF, not
optional polish. A reader notices their absence immediately (a blank page, a
title-less cover, a wall of unexplained jargon, dead citation text). Apply them by
default; only skip one if the user opts out or it genuinely doesn't fit the
content. (Slide decks — `bgn-deck`/`claudecode-deck`/`kawaii-storybook` — are
exempt from blank-page stripping and the glossary; the rest still help.)

1. **No blank pages.** The `book` class inserts filler pages (header + folio only)
   to open chapters on a recto, plus the odd trailing page. After every build, run
   `scripts/strip_blank_pages.py` on the output (Step 7) so the reader never hits
   an empty sheet.
2. **Use callouts/quotes/plain-English where they help.** The handbook ships
   `::: note` · `::: tip` · `::: warning` · `::: plain` ("In Plain English") ·
   `::: pullquote` (a large navy quote) · `::: do`/`::: dont` · `::: cheatsheet`.
   Add a `::: plain` box wherever a section leans on jargon so a non-expert can
   follow; pull a memorable sentence into a `::: pullquote`; flag traps with
   `::: warning`. These break up dense prose and are the difference between a wall
   of text and a guide.
3. **Add SVG diagrams to aid comprehension.** A roadmap, pipeline, comparison, or
   "how it works" flow lands far better as a picture. Author at least the key
   one(s) as hand-written raw SVG (Step 5). A timeline/roadmap and an architecture
   pipeline are the highest-leverage diagrams for most reports.
4. **Make external citations clickable, colored like a link.** Author every
   external source as a markdown link with descriptive text — `[Amazon Ads MCP
   beta](https://…)`, not a bare URL or plain text. The handbook template renders
   `urlcolor=NavyBlue` (external links blue + clickable) and `linkcolor=black`
   (internal TOC stays clean), so a proper markdown link becomes an href-styled
   citation automatically. Bare URLs do NOT auto-link in pandoc — they render as
   dead text, so always use `[label](url)`.
5. **Cover (page 1) must carry the title.** The cover is `[logo] → COMPANY → title
   → subtitle → author → date + version`, drawn by `titlepage.tex`. It pulls
   `title`/`subtitle`/`version` from the source **front-matter** — so if those are
   missing the cover renders blank/title-less. Confirm the front-matter has at
   least `title:` (recommend a `subtitle:` and `version:` too) before building; if
   the source has none, propose a title/subtitle and add them (Step 1).
6. **Author/colophon (page 2).** `titlepage.tex`'s `\dsauthorpage` prints a
   colophon (company, author, email, website, copyright, confidentiality) from the
   chosen org profile automatically — nothing to author, but verify the chosen
   org's profile fields are filled so the page isn't sparse.
7. **Glossary for jargon-heavy docs.** End long/technical documents with a short
   `## Glossary` — a two-column term/meaning table. It makes the document usable by
   readers outside the immediate domain and is cheap to add.

Tight-list gotcha: in pandoc, a bullet/numbered list **must** be preceded by a
blank line. A bold lead-in immediately followed by `- item` (no blank line)
collapses into one run-on paragraph. Ensure a blank line before every list.

## Step 0 — first-run config
If `~/.docsmith/profile.yaml` does not exist, create it (this drives identity +
branding for every document) and tell the user where it is:
```
mkdir -p ~/.docsmith/template ~/.docsmith/cache/diagrams
```
The profile is a **YAML list of self-contained org objects** — each entry is one
organization the make-pdf skill can brand a document as, and one is picked per
run by `company`. Every entry carries its own `company`, `author`, `email`,
`logo`, `wordmark`, `website`, `default_confidentiality`, and `copyright`, e.g.:
```yaml
- company: "Acme Corp"
  author: "Docs Team"
  email: "docs@acme.example"
  logo: "~/.docsmith/logo/acme.png"   # this org's own logo
  wordmark: ""                         # text fallback when no logo
  website: ""
  default_confidentiality: "Confidential"  # Public/Internal/Confidential/Restricted; "" = none
  copyright: "© 2026"
```
Ask the user for `company`/`author` if you don't know them; leave the rest blank
otherwise. A per-document front-matter or `--profile`/`--company`/`--logo`
always overrides these. (Legacy DICT profiles — a single flat org, or a
top-level `company` list paired with a `logos:` map — are still read by
`build.py` for back-compat, but new profiles should use the list-of-orgs form.)

## Step 1 — read the source
Read the source markdown. Parse its YAML front-matter:
- `template:` → the default target. (`templates: [..]` from older sources is still
  read; since one template builds per run, treat its first entry as the default.)
- title/subtitle/date/version etc. → document metadata.
If the user named a template in their request, prefer that.

**Cover check (checklist #5):** the cover pulls `title` (and ideally `subtitle`,
`version`) from front-matter. If the source has no `title:`, the cover renders
title-less — propose a title + subtitle and add a front-matter block before
building. While here, also plan the document-style checklist: are there sections
that need a `::: plain` explainer, a concept that wants a diagram (Step 5), bare
URLs that should become `[label](url)` links, and (for long docs) a `## Glossary`?

## Step 2 — doctor
Run `python3 "$PLUGIN_DIR/scripts/doctor.py"`. If a required tool is missing,
surface the install hint and stop.

## Step 3 — choose ONE template (HITL)
List the available templates (`ls "$PLUGIN_DIR/assets/templates"`). For each one,
read its one-line style summary from `assets/templates/<name>/template.yaml` (the
`description:` field) so the chooser shows *what each template looks like*, not just
its name. Use **AskUserQuestion with `multiSelect: false`** — "Render to which
template?" — passing each template as an option (label = template name, description
= its `template.yaml` `description`), with the front-matter default pre-selected.
Exactly one template is built per run. (Skip the prompt only if the user already
named exactly one template.)

## Step 4 — choose ONE company (HITL)
The profile is a LIST of org objects so one identity can brand many orgs. Read
`~/.docsmith/profile.yaml` and use **AskUserQuestion with `multiSelect: false`** —
"Brand this document as which company?" — offering each org entry's `company` as
an option (pre-select the first). A document brands exactly one company, so this
is single-select. (Skip the prompt only if the profile has a single org, or the
user already named one.)

Pass the chosen name to `build.py` in Step 6 as `--company`. **You do not resolve
a logo here** — `build.py` looks up the chosen org in the profile list and pulls
that org's own `logo`, `author`, `email`, etc. automatically. (Only pass
`--logo` if the user explicitly wants to override the org's logo for this one
document.)

## Step 5 — diagrams (hand-written raw SVG)
Diagrams are authored as **hand-written raw SVG** — plain XML (`<rect>`, `<line>`,
`<text>`, `<path>`, `<polygon>`, `<circle>`) with manual coordinates. **No d2, no
Mermaid, no image generation.** Keep the `.svg` files beside the doc (e.g. a
`diagrams/` folder) and embed each via a markdown image with an ABSOLUTE path:
    ![Caption](/abs/path/diagrams/funnel.svg){width=80%}
There is no pre-render step: the handbook (pandoc+tectonic) auto-converts SVG→PDF
via `rsvg-convert`, and decks (marp) embed SVG via Chrome. Omit `--diagrams-manifest`.
(Absolute paths are required — the build runs from a temp dir, so relative image
paths won't resolve. The image alt text becomes the figure caption.)

**Add diagrams by default (checklist #3):** for an explanatory document, don't ship
pure prose — author at least the key diagram(s). The highest-leverage ones are a
**roadmap/timeline** and an **architecture/pipeline** flow; comparisons and
"how it works" loops also land far better as a picture. **Validate each SVG before
embedding** with `rsvg-convert -f pdf -o /tmp/x.pdf diagrams/x.svg` — a malformed
SVG fails the build. Use the brand palette (navy `#003060`, amber `#E0821A`,
violet `#5A3A8A`, green `#1A7A3A`) on a white background so diagrams match the page.

## Step 6 — build the template
Build the one chosen template, passing the `--company` chosen in Step 4 (build.py
resolves that org's logo/author/etc. from the profile). Spawn a
**template-builder** subagent with `SOURCE`, `PLUGIN_DIR`, `TEMPLATE`, an `OUT`
path (default `<source-dir>/<source-stem>.<template>.pdf`), the chosen
`--company`, an optional `--logo` only if the user is overriding the org's logo,
and `PROFILE` if the user supplied one.

If subagents aren't available, run the build directly:
```
python3 "$PLUGIN_DIR/scripts/build.py" --in "$SOURCE" --out "$OUT" \
  --template "$TEMPLATE" \
  --company "$COMPANY"
```
(Add `--logo "$LOGO"` only to override the chosen org's own logo.)

## Step 7 — strip blank pages, then report
**First (checklist #1), strip blank/filler pages** from the freshly built PDF:
```
python3 "$PLUGIN_DIR/scripts/strip_blank_pages.py" "$OUT"
```
It removes pages that carry only a running header + folio (keeps the cover, and
refuses to drop >40% as a safety net), in place. This runs on every handbook
build because the `book` class reliably inserts filler pages; decks don't need it.

Then **report** the output PDF with its final page count and size. If the build
failed, surface its error. Mention that the authoring conventions live in
`references/authoring-guide.md`.

Before declaring done, sanity-check the document-style checklist held: cover has a
title, citations are links (not dead text), key diagrams are present, and (for long
docs) there's a glossary. If you can, render a couple of pages to PNG
(`pdftoppm -png -r 90 -f N -l N "$OUT" /tmp/check`) and eyeball the cover + a
content page — image review catches a title-less cover or uncolored links that
text checks miss.

## Authoring quick reference
- Front-matter selects `template(s)` + metadata (`title`/`subtitle`/`version` feed the cover); `overrides:` tweaks tokens per-doc.
- Diagrams: hand-written raw SVG (plain XML — <rect>/<line>/<text>/<path>/<polygon>, manual coordinates; no d2/Mermaid/image-gen), embedded via `![Caption](/abs/diagram.svg){width=80%}`. Validate with `rsvg-convert` before building.
- Handbook callouts: `::: note` / `::: tip` / `::: warning` / `::: plain` ("In Plain English") / `::: do` / `::: dont` / `::: cheatsheet` / `::: pullquote`.
- Citations: write external sources as markdown links `[label](url)` so they render blue + clickable (bare URLs become dead text). Always put a blank line before a list.
- Long docs: end with a `## Glossary` term/meaning table; after building, strip blank pages with `scripts/strip_blank_pages.py` (Step 7).
- Decks: separate slides with `---`; pick a layout per slide with `<!-- _class: kpi -->` (cover, kpi, split, quote, versus, statement, closing, …). `kawaii-storybook` adds `path` (+ `accept`/`reject`/`caution`), `laws`, `scorecard`, `flow`, `scenarios`, `roadmap`, `figure`, and renders emoji 🐻🦊🦉🐹 as mascots.
See `references/authoring-guide.md` for the full contract and
`references/adding-a-template.md` to add a new template.
