---
name: design-fundamentals
description: >
  Say why a design looks wrong, and what to change. Use this whenever something visual "looks off",
  "looks cheap", "feels amateurish", or "doesn't look professional" and the person cannot name why —
  and whenever someone needs colours, fonts or a layout chosen for them. Runs a measured review over
  colour, type, layout, grouping and hierarchy, then reports concrete fixes ranked by impact with a
  severity each; or turns a brief into a buildable spec — palette with hex and 60/30/10, a type
  pairing with real sizes off a scale, a grid. Checks the contrast maths people skip, including
  borders and other non-text elements (3:1), not just text (4.5:1). Scope is **print and static
  graphic design**: posters, flyers, packaging, labels, menus, signage, banners, book and album
  covers, logos and wordmarks, slide decks, social posts and thumbnails. Reach for it on phrasings
  like "why does this poster look cheap", "our deck cover feels amateurish", "these two brand
  colours fight each other", "what pairs with Montserrat ExtraBold", "pick a palette and fonts for
  my cafe menu", "the negative space in our logo isn't reading", "this packaging looks like a
  supermarket own-brand", "give this junior useful feedback on their flyer" — even when no design
  principle is named, and even though a design answer could be improvised without it. Improvising is
  exactly the problem: unaided answers skip the contrast measurement, invent sizes instead of
  deriving them, and repeat folklore like the golden ratio being inherently beautiful. Do NOT use
  for websites, web pages, app or product UI, dashboards, or components — `impeccable` and
  `frontend-design` own the interface layer, and they cover critique as well as building. Nor to
  render markdown into a PDF (docsmith's `make-pdf`), generate images or logos, or pick chart-series
  colours (`dataviz`).
---

# dkv — design fundamentals

A working design-review method, checked against the literature rather than assembled from received
wisdom. The theory lives in five reference files; this file decides which one you need and how to
turn it into an answer.

Two things make this more useful than reciting principles. First, the reference files carry the
**numbers** — contrast ratios, measure, leading, scale ratios — so feedback is specific rather than
"add more contrast". Second, they mark the claims that are **⚠ contested**: popular design advice
contains a lot of confidently-repeated folklore, and passing it on unqualified is how you give
advice that sounds authoritative and is wrong.

## The numbers, inline

These come up in almost every review, so they live here rather than behind a file read. Most
critiques never need to open a reference at all.

| | |
|---|---|
| Contrast, body text | **≥ 4.5:1** · large text (18pt / 14pt bold) **≥ 3:1** |
| Contrast, non-text | **≥ 3:1** — borders, focus rings, icons, chart strokes (WCAG 1.4.11). The commonly-missed one |
| Colour alone | never the only carrier of meaning — always pair with label, icon, shape or position |
| Typefaces | **2–3 maximum**; weights within one family are free |
| Measure (line length) | **45–75 characters**, ~66 ideal; 40–60 on screen |
| Leading | **120–150%** of size for body; tighter (1.0–1.2) for headlines |
| Palette proportion | **60 / 30 / 10** — and the real contrast sits between the 60 and the 30 |
| Type scale | pick a ratio and stick to it: 1.2 / 1.25 / 1.333 conservative → dramatic; φ 1.618 gives only ~4 usable steps |
| Screen spacing | multiples of **8** |

## Router — one file, occasionally two

Open a reference when you need the *reasoning* behind one of these, or when the question goes
beyond them. Each file is sectioned, so cite `references/color.md` §3 rather than reading around.

| The question / symptom | Read |
|---|---|
| Palette, colour scheme, "these colours clash", brand colour, print vs screen, colour meaning | `references/color.md` |
| Font choice, pairing, "what goes with X", scale, body copy looks messy | `references/typography.md` |
| Composition, placement, grid, alignment, white space, "it looks empty/cramped", balance | `references/layout.md` |
| Grouping, "these don't look related", scan order, logo negative space, what the eye sees first | `references/gestalt.md` |
| Which principle applies to a symptom you can't name yet | `references/principles.md` — index only, ~60 lines |

**A vague brief is not a licence to read everything.** "Something feels off", "review this", "give me
a direction" are the *most* common openings, and they tempt you to load all five files just in case.
Don't: look at the artifact first, let it tell you which one or two axes are actually failing, then
open those. Reading five files to produce one critique costs a large multiple of the tokens and
reliably produces a worse answer — a flat recital of every principle instead of a judgement about
this piece. **If you have opened three, stop and write.**

Accessibility detail is `references/color.md` §8. Reading patterns (F/Z) are `references/gestalt.md`
§2, not layout.

## Mode A — Critique

When there is an existing design: an image, screenshot, deck, URL, or a description of one.

1. **See all of it before judging any of it.** For anything longer than one screen — a scrolling
   page, a multi-slide deck, a set of screens — enumerate the parts first (from the source, a
   section list, or a full-page capture), then confirm you have actually viewed each one. Scrolling
   in big jumps and reporting on what you happened to land on produces a confident-looking list with
   silent holes, and the reader cannot tell which parts you never opened. **State your coverage and
   viewport in the answer** — "at 1440×900, all seven sections" is checkable; a bare list of findings
   is not. If you did sample, say which parts you skipped. An honest partial review is useful; an
   unmarked one is misleading, because "no findings there" and "I never looked" are indistinguishable.
2. **Look for stated intent.** Source files and captions often carry the designer's reasoning —
   comments, notes, a line of copy explaining an unusual choice. Read it before calling anything
   broken. An uneven grid the caption explains, or a spacing decision documented in a comment, is a
   *decision you are reviewing*, not a mistake you are catching. Disagree if you have grounds, but
   argue with the reasoning rather than reporting it as an accident.
3. **Name what the piece is** — medium, audience, and what it is trying to make the viewer do. A
   critique that ignores the brief just imposes taste; a dense wholesale price list and a luxury
   perfume poster fail completely different tests.
4. **Run the review pass** below, reading the reference sections it points to.
5. **Report.** Lead with the two or three highest-impact problems, then the rest. A critique nobody
   acts on is worthless, and a flat list of fifteen findings does not get acted on.

**Measure before you trust your eye, and say which won.** Contrast, spans, sizes and margins are all
checkable against the source — do that rather than judging from the render. Your impression is a
hypothesis: a colour that looks too dim may measure fine, and a grid that looks ragged may sum
exactly. When a measurement overrules your impression, report the measurement and note that it did,
because "this looked wrong and isn't" is information the reader needs.

**A finding someone else reports is a hypothesis too.** If a claim arrives from another review, a
colleague, or a previous session, verify it against the artifact in front of you before repeating or
fixing it. Files change, and a real finding about last week's version is a false one today.

Use this shape:

```
**What this is:** <one line — medium, audience, job>

**Fix these first**
1. <problem> — <why it matters here> → <specific fix>
2. ...

| Element | Principle | Problem | Fix | Severity |
|---|---|---|---|---|
```

Severity is `high` when it breaks legibility or the message, `medium` when it weakens them, `low`
for polish. Anything failing the contrast floor (`color.md` §8) is `high` — that is measurable, not
a matter of taste.

## Mode B — Direction

When there is a brief but no design yet. Produce something concrete enough to build from, not
adjectives:

- **Palette** — the scheme (`color.md` §2), hex values, the 60/30/10 assignment (§3), and the
  **measured contrast ratio** for every text-on-background pair you propose. State the audience
  you assumed, because colour meaning is cultural (§5).
- **Type** — two faces with their categories and roles (`typography.md` §2–3), a scale ratio with
  the actual sizes, and the measure and leading for body copy (§4–5).
- **Layout** — the grid (`layout.md` §5), alignment strategy (§4), and where the focal point sits
  and why (§2).
- **Rationale** — which grouping and movement decisions you are relying on (`gestalt.md`,
  `layout.md` §7).

## The review pass

Work in this order. It runs cheapest-to-check first, and roughly in the order a viewer's eye does.

1. **Legibility floor** — body text ≥ 4.5:1, large text ≥ 3:1, and **non-text ≥ 3:1: component
   borders, focus rings, icons, chart strokes** — any boundary the user must perceive (WCAG 1.4.11).
   Check the non-text cases explicitly; they are the ones reviews miss, because a button whose label
   passes at 13:1 can have a border at 2:1, and the border is what tells you the button is there.
   Then: is any meaning carried by colour alone? (`color.md` §8)

   Run the numbers rather than judging from the render — `scripts/contrast.py` takes a pair
   (`python3 scripts/contrast.py "#713946" "#270710" ui`) or a TSV of them via `--pairs`, and reports
   the verdict against the threshold that applies. *This is pass/fail, not preference — check it
   first so you never approve a beautiful unreadable thing.*
2. **Colour** — is there an identifiable scheme, or arbitrary colours? Is the 60/30/10 proportion
   deliberate, with real contrast between primary and secondary? (`color.md` §2–3)
3. **Type** — 2–3 faces at most? Does the pairing have genuine contrast and a shared mood? Is the
   size hierarchy from a scale? Is the measure 45–75 characters and the leading 120–150%? Any
   stretched type, widows, or rivers? (`typography.md` §2–6)
4. **Layout** — is there a grid? Is everything aligned to something, or only nearly? Is white space
   distributed deliberately? Where does the focal point sit? (`layout.md` §2–6)
5. **Grouping** — do the visual groups match the meaning? Any accidental container or connector
   grouping unrelated things? (`gestalt.md` §3, §9–11)
6. **Hierarchy and movement** — can you name the single most important element? Does the eye reach
   it first, and where does it go next? (`principles.md` §4, `layout.md` §7)
7. **Simplicity** — what can be removed without losing the message? (`principles.md` §2)

## Notes

**Rules break for a reason, not by accident.** This framing is the difference between a useful
critique and a checklist bot. When a design violates a principle, name
the principle, then ask whether the break is deliberate and buying something. Experimental and
editorial work breaks alignment, hierarchy and palette rules constantly and is better for it;
corporate and functional work rarely is. Flag the deviation, judge it against the brief.

**Colour meaning is cultural, so state your assumption.** The associations in `color.md` §4 are
learned, not universal, and several of them invert across cultures. Say "for a Western consumer
audience, blue reads as trustworthy" rather than "blue means trust". If you know the actual audience,
use it.

**Qualify the contested claims, don't parrot them.** Four are marked ⚠ in the references — the
golden ratio as a law of beauty, pink lowering heart rate, the 80% brand-recognition figure, and
60/30/10's empirical status. Each remains *useful*; none is established fact. When one comes up, give
the useful part and say plainly what is not supported. Design advice that repeats folklore
confidently is the failure mode this skill exists to avoid.

**Font pairing depends on taste and experience.** The example pairings in `typography.md` §3 are
illustrative, not prescriptive. When a pairing feels subtly wrong and you cannot say why, compare
x-heights first.
