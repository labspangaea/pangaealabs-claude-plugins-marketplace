# corporate-deck — slide classes

Every slide class in the `corporate-deck` design system, rendered once in
`acme-qbr.pdf` (19 slides, 1440×810pt, FY26 Strategy Review). One row per class,
in the order they appear in the deck.

Every content slide carries the footer **Acme logo** (the navy "A" mark from the
profile's `logo: examples/logo/acme.png`) plus `Acme Corp · Jane Rivera · © 2026
Acme Corp` and a page number — except `cover` (1) and `closing` (16), which
intentionally suppress the footer and folio.

| Class | What it is | Slide |
|---|---|---|
| `cover` | Centered title slide — eyebrow, big *accent* headline, subtitle, brand logo; no footer/folio. | 1 |
| `agenda` | Numbered cards (decimal-leading-zero gold counters); turns a list into a 3-up "what we'll cover". | 2 |
| `bigstat` | One oversized headline number (200px) with a small *accent* unit; a single supporting paragraph. | 3 |
| `kpi` | 3-up metric cards, each with a huge value; the middle card is inverted to brand navy. | 4 |
| `pillars` | 2-up cards, bold title + description — the load-bearing strategic pillars. | 5 |
| `cards3` | 3-up cards, bold title + description — a flat "three things" grid. | 6 |
| `compare2` | Two side-by-side cards comparing two states/periods (FY24 vs FY25). | 7 |
| `split` | Content flows while a hand-written SVG figure floats right with **no box** (it carries its own framing). | 8 |
| `steps` | 3-up cards read as an ordered process (Discover → Build → Scale). | 9 |
| `people` | 2×2 cards, each pairing a portrait SVG avatar with a name + role (the leadership team). | 10 |
| `versus` | Two cards where the first is "before" (red, dashed) and the last is "after" (green/gold). | 11 |
| `timeline` | 4-up cards as a chronological arc, bold year + milestone. | 12 |
| `logowall` | 4-up cards, each holding a partner logo SVG + wordmark ("trusted by"). | 13 |
| `quote` | Large centered Lora-italic blockquote; **bold**/*accent* runs turn gold. | 14 |
| `statement` | Dark navy slide — white headline with a gold *accent*; a thesis line. | 15 |
| `closing` | Dark navy sign-off — gold-accent headline + contact line; no footer/folio. | 16 |
| `stack` | Heading, then a large centered SVG figure (roadmap), then a green-spined `>` callout. | 17 |
| `iconcards` | 3/4-up cards, each with a small SVG icon pinned left and title + description beside it. | 18 |
| `procon` | A two-card pair tinted success-green (first) / danger-red (last) — the pricing decision. | 19 |

**Footer logo:** sourced from the docsmith profile (`--company "Acme Corp"` →
`examples/logo/acme.png`), composed by `build.py` as `![h:40](…/acme.png)` and
rendered bottom-left on every slide except `cover` and `closing`.
