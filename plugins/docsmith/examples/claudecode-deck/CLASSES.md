# claudecode-deck — slide classes

The `claudecode-deck` template (warm cream/clay, editorial Anthropic/Claude
style) renders 16:9 slides at 1440×810pt. This deck — **Nimbus — Product
Launch** — exercises every one of the 22 slide classes once, each on its own
slide. Set the class with an HTML comment at the top of a slide:
`<!-- _class: NAME -->`.

The **footer** is auto-composed by `build.py` from the active profile
(`logo · company · author · copyright`) and pinned to the same bottom band as
the page number. Every slide here renders the **Nimbus Studio** logo at left
followed by `NIMBUS STUDIO · LEE PARK · © 2026 NIMBUS STUDIO`. On the dark
`statement` slide the logo is inverted to stay legible.

| Class | What it is | Slide |
| --- | --- | --- |
| `cover` | Title slide — oversized serif headline (`*accent*` → clay italic), eyebrow, and lead paragraph, vertically centered. | 1 |
| `agenda` | 3-up card grid with auto mono leading-zero numbers (`01 ·`, `02 ·`, …) — the runsheet / table of contents. | 2 |
| `bigstat` | One headline stat at 220px — a single number carries the slide. | 3 |
| `kpi` | 3-up cards, each a large serif value + caption; middle card peach-highlighted. | 4 |
| `pillars` | 2-up cards for a small set of core promises; `li strong` is the card title. | 5 |
| `cards3` | 3-up neutral card grid; middle card peach-highlighted. | 6 |
| `compare2` | 2-up cards comparing two options side by side. | 7 |
| `models` | 3-up cards for tiers/plans/models; middle card peach-highlighted. | 8 |
| `people` | 2-up cards for team members / roles (name + bio per card). | 9 |
| `glossary` | 4-up compact cards defining short terms. | 10 |
| `filegrid` | 4-up cards for files/modules in a project layout (e.g. `nimbus.toml`, `handlers/`). | 11 |
| `featurepair` | 2-up cards — two halves of one idea (e.g. submit-time vs run-time). | 12 |
| `compare3` | 3-up cards comparing three paths/options to one destination. | 13 |
| `versus` | 2-up before/after — first card muted (before), last card peach + clay (after). | 14 |
| `split` | Heading + body left, a content figure floated right on the cream wash (no white card); supports a `>` callout pill. | 15 |
| `steps` | 3-up cards for an ordered how-to / get-started sequence. | 16 |
| `iconcards` | Cards with a small clay-stroke SVG icon pinned left + title/desc stacked beside it (`- ![](/abs/ic-x.svg) **Title** desc`). | 17 |
| `stack` | Heading on top, a large centered full-width figure below, then an optional caption or `>` callout. | 18 |
| `procon` | 2-up card pair where the contrast IS the point — first tinted success-green (pros/do), last error-red (cons/don't). | 19 |
| `quote` | Big centered serif italic pull-quote; `**bold**`/`*em*` render in clay. | 20 |
| `statement` | Dark espresso full-bleed slide for a single bet/thesis; footer logo auto-inverts. | 21 |
| `closing` | Final call-to-action slide — oversized serif headline, centered. | 22 |

## Figures (transparent ground)

The `split`, `stack`, and `iconcards` figures are hand-written raw SVG embedded
by absolute path. Per the claudecode rule, figures on `split`/`stack` sit
directly on the cream wash with **no white card** — every SVG uses a
**transparent** ground (cream/surface/peach/clay tokens, ink/clay strokes; never
`#fff`). All five SVGs in `diagrams/` validate with `rsvg-convert`:

- `diagrams/split.svg` — request lifecycle (edge → queue → workers → store), used on slide 15.
- `diagrams/stack.svg` — wide rollout timeline (alpha → beta → GA → multi-region), used on slide 18.
- `diagrams/ic-bolt.svg`, `ic-shield.svg`, `ic-globe.svg` — 64×64 clay-stroke icons for the `iconcards` slide 17.
