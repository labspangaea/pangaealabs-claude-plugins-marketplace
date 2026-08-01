# Product — `docs/` web surface

> **Scope.** This file governs the web pages under `docs/` — currently `index.html`, the
> explainer for the `dkv` plugin. It is **not** the repo-wide product doc. The root
> `PRODUCT.md` covers docsmith's PDF template design systems and opens by stating "this repo
> has no web frontend"; that was true when written and is no longer. impeccable's
> `context.mjs` reads the root file only, so anyone working on this surface must load this
> one deliberately.

## Register

**brand** — design *is* the product here. The page's job is to make someone understand a
design-review method well enough to decide whether they want it, and the page itself is the
proof that the method works. A page about graphic design that looks defaulted refutes itself.

## Users

- **Someone deciding whether to install `dkv`.** They have a poster, a menu, a deck that
  "looks off" and they cannot say why. They are not necessarily designers and will not know
  what *chroma*, *leading*, or *optical alignment* mean. Every term is defined before use.
- **A designer who wants the method, not the plugin.** They will check the numbers. If a
  contrast ratio on this page is decorative rather than measured, they will notice, and the
  page loses them permanently.

## Product Purpose

Explain `dkv` as a ladder: each part defines one term, and the next part is built from it.
By the last part the reader can run the review pass themselves. Success is a reader who can
look at their own poster and name what is wrong — whether or not they ever install anything.

## Brand Personality

**A measuring instrument, not a brochure.** The page performs what it describes: values are
printed next to the things they measure, margins are visibly set, figures carry their own
units. Confident, precise, unhurried. It does not sell; it demonstrates and lets the reader
conclude.

The voice inherits the plugin's defining habit — it marks what is *not* supported. Four
claims in `dkv` are flagged contested (φ as a law of beauty, Baker-Miller pink, the 80%
brand-recognition figure, 60/30/10's empirical basis). The page carries those forward. A
design explainer that repeats folklore confidently is the exact failure the plugin exists to
avoid.

## Aesthetic lane

**A press proof sheet.** Ink on stock, registration marks, measured margins, correction
values in the margin. A proof is a *working document* — it exists to be checked, not admired.

Mood: *a proof pulled at 6am — cold paper, one ink laid down wet, correction marks in the
margin, everything measured twice.*

Chosen against two reflexes, both named so they stay rejected:

- **First-order:** editorial-typographic (display serif, small mono labels, ruled columns,
  monochrome restraint). `brand.md` lists this as saturated, and it is where every design
  explainer drifts.
- **Second-order:** terminal / brutalist-utility — full mono, black, ASCII rules. The trap
  one tier deeper, and `brand.md` bans mono as shorthand for "technical".

Monospace appears **only on measured values** — ratios, pixel sizes, character counts. That
is a proof sheet's own convention for numbers, not a costume for the page.

## Colour strategy

**Committed** — one saturated ink carrying the page. `dkv`'s subject is print, and print has
ink. Seeded from `palette.mjs` at `oklch(0.550 0.180 20)`, a warm red: the hue proofing marks
and registration crosses have always been.

Surface is **pure white** (`oklch(1 0 0)`) in light mode. Not cream, not sand, not
warm-tinted near-white — that band is the saturated AI default, and a page about design
cannot afford it. Warmth lives in the ink, not the paper.

## Accessibility floor

The page's own subject matter, so it is held to it exactly:

- Body text **≥4.5:1**, set at ink — never muted grey for elegance.
- **Non-text ≥3:1** for anything required to read a figure: strokes, axes, marks, borders.
  Purely decorative hairlines are exempt under WCAG 1.4.11 and are tokenised separately
  (`--hair` vs `--stroke`) so the distinction is enforced rather than remembered.
- **Nothing meaning-bearing in colour alone.** Every figure encodes its meaning in shape,
  stroke style, or label as well — so it survives greyscale printing and colour-vision
  deficiency, which is what the plugin asks of everyone else.
- Measure **65–75ch**. Reduced-motion alternative for every figure, with no transform motion.
- Real `<text>` in every SVG, with `<title>`/`<desc>`. No baked raster text.

## Design principles

1. **The figure is the argument.** If a diagram can replace a paragraph, it does.
2. **Every number is measured.** Contrast ratios come from running the plugin's own
   `scripts/contrast.py`. Type sizes come from the real modular scale. If it cannot be
   measured, it is not printed.
3. **Define before use.** No term appears before its plain-language definition.
4. **The animation is the teaching.** Each figure animates the one transformation its part is
   about. A figure that animates without teaching anything extra is made static.
5. **Complete without motion.** Content is visible by default; animation is enhancement. A
   headless render or a screenshot shows a finished page.
6. **Show the limit.** Where the method stops — print and static graphics, not motion, not
   product UI — is body text, not a footnote.

## Anti-references

- Cream / sand / parchment backgrounds.
- Gradient text, side-stripe borders, glassmorphism, identical card grids.
- A tiny uppercase tracked eyebrow above every section.
- Numbered markers as decoration. **Exception, deliberate:** the parts here are numbered
  because they *are* a sequence — each is built from the term the previous one defined, and
  reordering breaks the explanation. That is numbering as structure, which is what the ban
  exempts.
- Illustrative numbers. A ratio that was typed rather than computed is the worst possible
  failure on this particular page.
