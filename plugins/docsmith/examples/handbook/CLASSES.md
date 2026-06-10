# handbook — component classes

This example (`async-handbook.md` → `async-handbook.pdf`) is a complete catalog of
the `handbook` template: every component class the design system defines is
rendered at least once. Page numbers below are physical PDF pages in the rebuilt,
blank-page-stripped `async-handbook.pdf` (11 pages total).

| Component | What it is | Page |
|---|---|---|
| Title page / cover | Auto-generated navy cover: logo, company, title, subtitle, author, date, version | 1 |
| Colophon (`\dsauthorpage`) | "About this document" page listing the org's full profile (company, author, email, website, copyright, confidentiality) | 2 |
| Dotted-leader TOC | Auto `\tableofcontents` with navy chapter entries and dotted leaders | 3 |
| Chapter opener | Big navy numeral + navy rule + sans chapter title (Ch. 1 / 2 / 3) | 4, 6, 9 |
| `::: note` | Navy pill-tab "Note" card | 4 |
| `::: tip` | Amber "Pro Tip" pill-tab card | 5, 7 |
| `::: pullquote` | Large navy italic with thick navy left rule | 5 |
| `::: plain` | Violet "In Plain English" card | 5, 10 |
| `::: warning` | Deep-amber "Watch Out" card | 5, 10 |
| SVG figure | Hand-written raw SVG (async message lifecycle) embedded as a captioned figure | 6 |
| `::: do` | Green "Do" pill-tab card | 7 |
| `::: dont` | Red "Don't" pill-tab card | 7 |
| External links | Clickable in-text URLs rendered in uniform link-blue | 7 |
| Code block | Fenced ```` ```text ```` block styled as a tinted card with navy left rule | 7 |
| `::: cheatsheet` | Full-width red banner card ("Quick Reference") | 8 |
| `::: anchor` | Navy pill-tab card (anchor → same box as note) | 9 |
| `::: alert` | Full-width red banner card (alert → same box as cheatsheet; escalation/BLOCKING note) | 10 |
| Glossary | Two-column term/meaning table in the back matter | 11 |

Note: the footer brand mark, the cover, and the colophon all render the org logo
pulled from the profile (`examples/profile.example.yaml` → Acme Corp → `logo:
examples/logo/acme.png`); the footer reads "[logo] Acme Corp · Jane Rivera" on
every content page.
