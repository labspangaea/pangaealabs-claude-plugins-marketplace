# dkv — graphic-design fundamentals

**DKV** (*Desain Komunikasi Visual*) turns design theory into a working review method. One skill,
five reference files, no scripts and no dependencies — it is pure knowledge, loaded on demand.

## The skill

`/design-fundamentals` runs in two modes:

- **Critique** — hand it an existing design (image, screenshot, deck, URL, or a description) and it
  runs a structured review pass, then reports the two or three highest-impact problems first with
  concrete fixes and a severity per finding. A critique nobody acts on is worthless, so it does not
  hand back a flat list of fifteen equal-weight nitpicks.
- **Direction** — hand it a brief and it returns something buildable: a palette with hex values, the
  60/30/10 assignment and **measured contrast ratios**; a type pairing with roles and real sizes off
  a modular scale; a grid and alignment strategy; and the reasoning behind the placement.

It covers graphic design *and* UI — poster, social post, slide deck, thumbnail, packaging, logo,
landing page, dashboard, app screen. It does **not** write frontend code, render PDFs, or generate
images.

## What it covers

| File | Contents |
|---|---|
| `references/color.md` | hue/tint/shade/tone · wheel schemes · 60/30/10 · colour psychology · why meaning is cultural · RGB vs CMYK · warm/cool · **the WCAG contrast floor and colour-blind-safe palettes** |
| `references/typography.md` | kerning/tracking/leading/x-height · the six typeface categories and their permitted roles · pairing · modular scales · measure and leading numbers · the anti-pattern list |
| `references/layout.md` | golden ratio and Fibonacci · rule of thirds · active vs passive white space · alignment · the four grid systems (+ the 8pt grid) · balance · movement |
| `references/gestalt.md` | similarity · continuity (with the F/Z/layer-cake/spotted scan patterns) · proximity · figure–ground · common fate · closure · symmetry · Prägnanz · common region · uniform connectedness · **and what to do when two of them conflict** |
| `references/principles.md` | the cross-cutting index — CRAP, KISS, contrast, hierarchy, repetition — each pointing at the file where it is operationalised |

The router in `SKILL.md` means only the relevant one or two files are ever read.

## Sourcing

Checked against the literature rather than assembled from received wisdom, because a lot of
widely-shared design advice is folklore. Two things are marked inline:

- **⚠ contested** — popular but weakly supported. There are four, and they are the point:
  - *the golden ratio as a law of beauty* — traces to Adolf Zeising in the 1850s; no scientific
    support for φ driving aesthetic preference. It remains a perfectly good scale ratio, just not a
    special one.
  - *pink lowers heart rate* — Schauss (1979) and Baker-Miller pink; failed to replicate under
    controlled study, effect fades within ~15 minutes.
  - *colour increases brand recognition by 80%* — miscited; the underlying research was about colour
    in documents and graphs, and colour-vs-black-and-white advertising.
  - *60/30/10* — an interior-design heuristic with no empirical basis. Still a good default.
- **citations** — wherever a specific number is doing the work (WCAG ratios, the 45–75 character
  measure, NN/g's scan-pattern study, Müller-Brockmann's grid, Paoletti on pink and blue).

Everything unmarked is ordinary craft convention, and each file says so at the top.

## Usage

```bash
/plugin install dkv@pangaealabs-claude-plugins-marketplace
```

Then just ask — the skill triggers on design feedback and design-choice requests without being named:

```
why does this poster look off?                    → critique
critique the visual design of this screenshot     → critique
pick a palette and fonts for a coffee shop menu   → direction
what pairs with Montserrat Extra Bold?            → direction
is the hierarchy on this landing page working?    → critique
```
