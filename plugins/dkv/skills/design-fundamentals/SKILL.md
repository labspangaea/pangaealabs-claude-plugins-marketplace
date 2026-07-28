---
name: design-fundamentals
description: >
  Apply and critique graphic-design fundamentals — colour theory, typography, layout, grid systems,
  Gestalt principles, visual hierarchy — on any visual work: a poster, social post, slide deck,
  thumbnail, packaging, logo, landing page, dashboard or app screen. Two modes: CRITIQUE an existing
  design (name what is wrong against a structured review pass, with concrete fixes ranked by impact)
  or DIRECT a new one (a colour scheme with a 60/30/10 split and measured contrast ratios, a type
  pairing with a modular scale, a grid and alignment strategy). Carries the numbers most design
  advice omits — WCAG contrast floors, the 45–75 character measure, 120–150% leading, the 8pt grid —
  and flags popular-but-unsupported claims instead of repeating them. Use this whenever someone
  wants design feedback or design direction, even casually — e.g. "why does this poster look off",
  "critique my slide deck", "pick a colour palette for my cafe menu", "what font pairs with
  Montserrat", "make this flyer look more professional", "is the hierarchy on my landing page
  working", "these two colours feel wrong together", "review the visual design of this screenshot".
  Trigger on any request to review, improve, or make choices about how something LOOKS, even when
  the user names no principle. Do NOT use to write frontend code or CSS (that is `frontend-design` /
  `impeccable`), to render markdown into a PDF (that is docsmith's `make-pdf`), to generate images
  or logos, or to choose chart-series colours (that is `dataviz`).
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

## Router — read only what you need

Do not read all five files. Read the one or two that cover the question; each is sectioned so you
can cite `references/color.md` §3 rather than the whole file.

| The question / symptom | Read |
|---|---|
| Palette, colour scheme, "these colours clash", brand colour, print vs screen, is this readable | `references/color.md` |
| Font choice, pairing, "what goes with X", sizes, hierarchy scale, body copy looks messy | `references/typography.md` |
| Composition, placement, grid, alignment, spacing, "it looks empty/cramped", balance | `references/layout.md` |
| Grouping, "these don't look related", scan order, logo negative space, what the eye does first | `references/gestalt.md` |
| "It just looks off" with no specific symptom · a general review · which principle applies | `references/principles.md` first — it indexes the rest |

Accessibility questions (contrast, colour blindness) are in `references/color.md` §8. Reading
patterns (F/Z) are in `references/gestalt.md` §2, not layout.

## Mode A — Critique

When there is an existing design: an image, screenshot, deck, URL, or a description of one.

1. **Look before judging.** Name what the piece is, who it is for, and what it is trying to make the
   viewer do. A critique that ignores the brief just imposes taste — a dense data dashboard and a
   luxury perfume poster fail completely different tests.
2. **Run the review pass** below, reading the reference sections it points to.
3. **Report.** Lead with the two or three highest-impact problems, then the rest. A critique nobody
   acts on is worthless, and a flat list of fifteen findings does not get acted on.

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

1. **Legibility floor** — is body text ≥ 4.5:1 and large text ≥ 3:1 against its background? Is any
   meaning carried by colour alone? (`color.md` §8) *This is pass/fail, not preference — check it
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
