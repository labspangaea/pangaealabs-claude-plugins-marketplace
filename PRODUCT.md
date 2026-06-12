# Product

> Scope: this PRODUCT.md is for **docsmith's template design systems** — the visual
> identities behind the rendered PDFs (`corporate-deck`, `claudecode-deck`,
> `kawaii-storybook`, `concept-deck`, `handbook`). It is **not** about a website or app
> UI; this repo has no web frontend. The "interface" being designed is the document
> output and the CSS / theme / SVG-DNA conventions that produce it.

## Register

brand

## Users

Two layers, both real:

- **Operators (who touch the design system):** docsmith maintainers/agents and authors
  who run `/make-pdf`. They don't hand-design each document — they pick a template + a
  company and let the system carry the brand. The surface they actually design against is
  the template's tokens, slide classes, callout vocabulary, and SVG conventions in
  `assets/templates/<name>/` (`design-system.css`, `theme.css`, `design-system.md`,
  `icons.md`). One markdown source fans out to several PDFs via parallel subagents, so the
  contract has to hold across templates.
- **End audience (who receives the PDF) — the real bar the design is judged against:**
  - `corporate-deck` → executives, government/civic stakeholders (defaults copied from the
    BGN gov design system); formal review and projection settings.
  - `claudecode-deck` → developers and technical/product audiences; Anthropic/Claude-adjacent
    talks and write-ups.
  - `kawaii-storybook` → learners and general audiences; explainer / NotebookLM-style narration.
  - `concept-deck` → engineers reading a system/architecture reference (ByteByteGo idiom).
  - `handbook` → readers of a long-form book (roadmaps, guides), on screen or printed.

Context of use: the artifact is almost always viewed as a **PDF** — a marp/Chrome render
(decks) or a LaTeX book (handbook) — often **projected** (decks) or **printed, sometimes in
grayscale** (handbook). The viewer never sees the markdown source; only the rendered result
is the product.

## Product Purpose

docsmith turns one markdown source into professional, on-brand PDFs across a **library of
design-system templates**. Each template is a fully committed visual identity — not a theme
toggle — so the same content can render as a civic deck, a warm editorial deck, a pastel
storybook, a black-outline tech-doc, or a LaTeX book, and each one looks deliberately
designed *for that audience's idiom*.

Success = **a reader cannot tell the document was generated.** The output reads as the work
of a human designer fluent in that audience's visual language, with zero "AI made this"
tells. The design system — tokens, classes, callout/div vocabulary, SVG-DNA, and the
authoring contract — is the product; the rendered PDF is the proof.

## Brand Personality

System-level voice: **deliberate, idiomatic, anti-generic.** Each template commits hard to
one reference world and stays in its lane:

- `corporate-deck` — formal, institutional, trustworthy. Civic navy `#071e49` + green
  `#92d05d`, gold/sky accents, restrained.
- `claudecode-deck` — warm, editorial, confident. Cream `#F0EEE6` + clay `#B85838`,
  Instrument Serif italic accents, **no white cards**.
- `kawaii-storybook` — soft, friendly, playful. Cycled pastel washes, rounded puffy cards,
  Baloo 2 headlines, emoji mascots, verdict pills.
- `concept-deck` — precise, engineering, high-legibility. Flat near-white field, **bold
  black 4px outlines**, Poppins black titles, electric-blue signal accent, SVG-first;
  **depth from borders, not shadows.**
- `handbook` — classic, authoritative, book-like. Latin Modern serif, navy `#003060`,
  chapter openers, dotted-leader TOC.

Three words across the whole system: **committed · idiomatic · legible.**

## Anti-references

- **Anything that reads "AI-generated."** The fail state is a viewer thinking "*which* AI
  made this?" instead of "*how* was this made?"
- **Template convergence.** The five must NOT drift toward one shared look. A safe
  pastel-on-cream middle is the death of the system; each change must make a template *more*
  itself.
- **Diagram shortcuts.** No d2, no Mermaid, no image generation, no external/R2-hosted
  images. Every visual is hand-written raw SVG. A library-generated diagram is off-brand by
  definition.
- **Decorative glassmorphism / blurred shadows.** concept-deck bans shadows outright (they
  render as hard grey rectangles in PDF viewers); depth comes from bold black borders.
- **White panels on the warm editorial deck.** A white card reads as a pasted foreign asset
  on `claudecode-deck`'s cream wash — figures sit on the wash with transparent grounds.
- **Generic AI-default palettes.** The cream/sand/beige body band is normally a tell; where a
  template uses cream (`claudecode-deck`), it is a *specifically committed Anthropic
  reference*, not a default — don't generalize it to other templates.
- The shared impeccable **absolute bans** (side-stripe borders, gradient text, the
  hero-metric template, identical card grids, eyebrow-on-every-section, numbered-section
  scaffolding, text overflow) apply to every template's CSS *and* its SVG.

## Design Principles

1. **Identity-preservation wins.** Each template already committed to a real reference (BGN
   gov, Claude editorial, NotebookLM, ByteByteGo, the `ai-roadmap` book). Preserve and
   *sharpen* the committed identity. Reflex-reject / greenfield rules apply only when
   authoring a brand-new template — never to retune what already ships.
2. **One lane per template — never converge.** The value is five distinct worlds. Every
   change must make a template more itself, not closer to the others. Cross-template work
   raises a shared quality/accessibility *floor* without homogenizing the look.
3. **Legible at the medium.** The deliverable is a PDF, often projected or printed grayscale.
   Contrast (WCAG AA), grayscale-legibility, and colorblind-safe diagrams are hard
   constraints, not nice-to-haves. Respect PDF-viewer reality: no blurred shadows, explicit
   `width`+`height` on every embedded SVG, transparent grounds where the template requires.
4. **Hand-built visuals only.** Diagrams, charts, icons, mascots — all hand-written raw SVG
   following each template's SVG-DNA (`concept-deck/icons.md` is canonical for that template).
   No generators, ever. This is the single biggest anti-AI-slop lever.
5. **The authoring contract is part of the design.** Tokens, slide classes, the callout/div
   vocabulary, and the merge order (template default → `~/.docsmith/template/<name>.yaml` →
   profile → front-matter/overrides → CLI) are the interface authors design against. Keep it
   consistent across templates so one source fans out cleanly, and document any new class in
   the template's `design-system.md`.
6. **A repeatable bar for new templates.** Every new template lands at the same craft level:
   a named real-world reference, a committed palette/type pairing (not a reflex pick), a full
   slide-class set, an SVG convention, and passing the contrast/grayscale/colorblind floor
   before it ships.

## Accessibility & Inclusion

- **WCAG AA contrast in the rendered PDF.** Body text ≥ 4.5:1, large/bold ≥ 3:1, against its
  *actual* background. Watch the pastel washes/cards (`kawaii-storybook`, `concept-deck`) and
  any muted body grays. Verify on the rendered output, not on token values in isolation.
- **Colorblind-safe diagrams.** `concept-deck`'s multi-pastel card set and `kawaii-storybook`'s
  cycled chips must stay distinguishable *without relying on hue* — keep the bold black
  outlines/labels, vary shape and position, and never encode meaning in color alone.
- **Grayscale-legible.** Decks and the handbook must read when printed black & white: ensure
  tonal (not just hue) contrast between adjacent cards, eyebrows, and accents.
- No motion concerns (static PDF output); SVG and layout must not depend on color or hover to
  convey structure.
