# kawaii-storybook — slide classes

Every slide class in the `kawaii-storybook` design system, rendered once in
[`cloud-safety.md`](cloud-safety.md) → [`cloud-safety.pdf`](cloud-safety.pdf)
(28 slides, 1440×810pt). PNG exports live in [`pages/`](pages/). The footer on
every content slide carries the **Nimbus Studio** logo + author + copyright,
supplied by the `Nimbus Studio` entry in `examples/profile.example.yaml`
(`--company "Nimbus Studio"`).

| Class | What it is | Slide |
| :--- | :--- | :---: |
| `cover` | Title slide — eyebrow chip, Baloo 2 headline with clay accent, intro line | 1 |
| `agenda` | 3-up cards with mono decimal-leading-zero numbers (`01 02 03 …`) | 2 |
| `bigstat` | One giant accent number + supporting sentence | 3 |
| `kpi` | 3-up cards, each a big accent value (no chip) over a label | 4 |
| `pillars` | 2-up puffy cards; each `**bold**` lead becomes a pastel chip | 5 |
| `cards` | Auto-fit puffy card grid (here 2×2) for a flat list of items | 6 |
| `cards3` | 3-up cards with the middle card highlighted (amber wash) | 7 |
| `path accept` | Analysis layout: floated hero (SVG) + chip-cards + **green** verdict pill | 8 |
| `path reject` | Same analysis layout with a **red** verdict pill | 9 |
| `path caution` | Same analysis layout with an **amber** verdict pill | 10 |
| `compare2` | 2-up side-by-side comparison cards | 11 |
| `compare3` | 3-up side-by-side comparison cards | 12 |
| `versus` | Before (dashed / red chip) vs after (green border + green chip) | 13 |
| `laws` | 2×2 titled card grid | 14 |
| `steps` | 3-up sequential cards (a short procedure) | 15 |
| `scorecard` | Markdown table as a clipboard matrix (🟢🟡🔴) + `>` conclusion bar | 16 |
| `flow` | List → row of numbered "stop" cards joined by connector chevrons | 17 |
| `scenarios` | Rows of `**Stage** → **Action** → **Result**` (last row tints green) | 18 |
| `timeline` | 4-up era cards in a horizontal time sequence | 19 |
| `people` | 2×2 people/role cards (emoji portraits in the chip lead) | 20 |
| `roadmap` | Zig-zag numbered signpost cards | 21 |
| `figure` (`bare`) | Title + one large hero (hand-written SVG) sitting on the wash | 22 |
| `split` | Floated image/card on the right; here a fenced code card flows left | 23 |
| `pillars` (callouts) | 2-up layout hosting `tip` + `warning` `<aside>` callouts | 24 |
| `quote` | Centered Lora-italic pull quote rendered as a soft verdict pill | 25 |
| `statement` | Dark full-bleed statement slide with accent words | 26 |
| `closing` | Closing slide — eyebrow, headline, sign-off line + mascots | 27 |

A trailing colophon slide (no `_class`, page 28) closes the deck and also shows
the Nimbus footer logo.

## Notes

- **`path` has three verdict variants** — `path accept` (green, p8), `path reject`
  (red, p9), and `path caution` (amber, p10) — driven by the modifier on the
  `<!-- _class: path … -->` directive; the colour flows into the `>` verdict pill.
- **`figure` / `split` / `cover` / `path`** can take a hand-written raw SVG hero
  ([`diagrams/hero.svg`](diagrams/hero.svg), validated with `rsvg-convert`,
  embedded by absolute path) wherever a big emoji mascot would go. `figure bare`
  lets the transparent character sit directly on the pastel wash.
- **Footer logo** — the rounded clay Nimbus mark renders bottom-left on every
  slide (cover excepted), beside `Nimbus Studio · Lee Park · © 2026 Nimbus
  Studio`, from the profile's `logo: examples/logo/nimbus.png`.
