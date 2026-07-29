# dkv — graphic-design fundamentals

**DKV** (*Desain Komunikasi Visual*) turns design theory into a working review method. One skill,
five reference files, and one small script — no dependencies beyond Python 3.

## The skill

`/design-fundamentals` runs in two modes:

- **Critique** — hand it an existing design (image, screenshot, deck, URL, or a description) and it
  runs a structured review pass, then reports the two or three highest-impact problems first with
  concrete fixes and a severity per finding. A critique nobody acts on is worthless, so it does not
  hand back a flat list of fifteen equal-weight nitpicks.
- **Direction** — hand it a brief and it returns something buildable: a palette with hex values, the
  60/30/10 assignment and **measured contrast ratios**; a type pairing with roles and real sizes off
  a modular scale; a grid and alignment strategy; and the reasoning behind the placement.

Scope is **print and static graphic design** — posters, flyers, packaging, labels, menus, signage,
banners, book and album covers, logos and wordmarks, slide decks, social posts, thumbnails.

It deliberately stops at the interface layer. Websites, app and product UI, dashboards and
components belong to `impeccable` / `frontend-design`, which cover critique as well as building —
two skills fighting over the same prompt helps nobody. dkv also does not render PDFs (docsmith's
`make-pdf`), generate images, or pick chart-series colours (`dataviz`).

## What it covers

| File | Contents |
|---|---|
| `references/color.md` | hue/tint/shade/tone · wheel schemes · 60/30/10 · colour psychology · why meaning is cultural · RGB vs CMYK · warm/cool · **the WCAG contrast floor and colour-blind-safe palettes** |
| `references/typography.md` | kerning/tracking/leading/x-height · the six typeface categories and their permitted roles · pairing · modular scales · measure and leading numbers · the anti-pattern list |
| `references/layout.md` | golden ratio and Fibonacci · rule of thirds · active vs passive white space · alignment · the four grid systems (+ the 8pt grid) · balance · movement |
| `references/gestalt.md` | similarity · continuity (with the F/Z/layer-cake/spotted scan patterns) · proximity · figure–ground · common fate · closure · symmetry · Prägnanz · common region · uniform connectedness · **and what to do when two of them conflict** |
| `references/principles.md` | the cross-cutting index — CRAP, KISS, contrast, hierarchy, repetition — each pointing at the file where it is operationalised |

The router in `SKILL.md` means only the relevant one or two files are ever read.

`scripts/contrast.py` computes WCAG ratios and reports the verdict against the threshold that
applies — including **`ui` (3:1) for non-text**: borders, focus rings, icons, chart strokes. That
case is the one reviews miss, since a button label can pass at 13:1 while its border fails at 2:1,
and the border is what tells you the button is there. Run `--selfcheck` to verify it.

## Sourcing

The point of this plugin is **consistency**, not secret knowledge. A capable model already gives good
design advice; what it does not do reliably is state its audience assumption every time, always check
contrast against a real floor, always derive sizes from a named scale, and always structure a
critique so the top three fixes are obvious. This makes those the default rather than the good day.

The content is checked against the literature rather than assembled from received wisdom, because a
lot of widely-shared design advice is folklore. Two things are marked inline:

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
this packaging looks own-brand, what's wrong?     → critique
```
