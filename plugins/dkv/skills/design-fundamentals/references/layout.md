# Layout

> Proportion, placement, white space, alignment, grid systems, balance, and movement.
>
> Unmarked statements are ordinary craft convention. **⚠ contested** marks something widely repeated
> but weakly supported.

## 1. Golden ratio and Fibonacci

φ ≈ **1.618**, and the Fibonacci sequence (1, 1, 2, 3, 5, 8, 13, 21…) approaches it. Three uses:

- **Splitting a layout** — divide the canvas by Fibonacci proportions (e.g. 8:13 rather than 1:1) to
  get an asymmetric split that feels intentional rather than undecided.
- **The golden spiral** — overlay it and place the focal object at the tightening centre, running
  secondary elements outward along the curve. In practice this is a placement heuristic that produces
  a strong off-centre focal point; §2 does the same job with less ceremony.
- **The golden circle** — nested circles at φ proportions as construction geometry for logo marks,
  giving consistent curve relationships across a mark.

For type sizes, φ is one scale ratio among several — see `typography.md` §4, which also carries the
⚠ contested note on φ as a supposed law of beauty. The short version: **use it because it produces a
strong asymmetric proportion, not because it is mathematically beautiful.** That claim does not hold
up, and the design works just as well without it.

## 2. Rule of thirds

Divide the frame into a 3×3 grid and place key elements on the four intersections, or along the
lines. Dead-centre placement reads as static and formal; a third-point reads as dynamic and leaves
room for the subject to face into.

This is the cheapest composition fix available and it is why it is worth reaching for before the
golden spiral — same off-centre benefit, no construction required. Centre placement is still correct
when you *want* stillness, formality or symmetry (§6).

## 3. White space

Negative space is not leftover room — it is oxygen for the design. Two kinds, and conflating them is why "add more white space" is unhelpful advice:

- **Passive white space** — the breathing room around and between elements: margins, gutters,
  leading, padding. It does the work of legibility and calm. Mostly invisible when correct.
- **Active white space** — space deliberately shaped to do a job: isolating a single element to
  make it the focal point, creating a deliberate pause, or forming an implied shape between objects.
  It is a compositional element in its own right.

How much you use is a function of the concept. Applying KISS (`principles.md` §2) pushes towards
more white space, because the fastest way to simplify is to remove things and let what remains
breathe. A dense editorial spread and a luxury brand poster can both be right.

## 4. Alignment

Every element should sit on a line shared with something else. The alignment does not have to be
visible — it has to be *findable*.

- **Edge alignment** (left or right) gives a hard invisible line and reads as structured,
  purposeful, modern. Left-aligned body text is the default for a reason: the eye returns to a
  predictable place each line.
- **Centre alignment** reads as formal, ceremonial, classical. It is weak for body copy — both edges
  are ragged, so the eye has no fixed return point — and strong for short, symmetric statements.

You can run one alignment throughout, two in deliberate opposition, or mix — but a mix has to look
chosen. The failure mode is elements that are *almost* aligned, which reads as carelessness rather
than as intent.

This is the small detail that separates beginner work from experienced work, and it matters most in **corporate and formal work**. Experimental design can
break alignment deliberately — but see the note at the end of `typography.md` §6 about breaks needing
a reason.

## 5. Grid systems

The modern grid comes from Josef Müller-Brockmann, who first presented his system in 1961 and
codified it in *Grid Systems in Graphic Design*. His key move: derive every module from the
**baseline text grid**, so the vertical rhythm of the type governs the whole layout rather than being
fitted into it afterwards. His systems run from 8 to 32 fields.

| Grid | Shape | Use for |
|---|---|---|
| **Manuscript** | one column | continuous prose — books, essays, long articles |
| **Column** | 2+ vertical columns | newspapers, magazines, most web layouts |
| **Modular** | columns + rows → a field matrix | catalogues, dashboards, anything with repeating cards |
| **Hierarchical** | irregular zones sized by importance | posters, landing pages, bespoke compositions |

Grid application is effectively endless — a grid can be rotated and run diagonally, which is a
standard way to get energy into a poster while keeping underlying structure.

**For screen work, the 8pt grid** is the modern default: size and space every element in multiples
of 8 (8, 16, 24, 32, 48…). It comes from Google's Material Design (2014) and spread industry-wide
after Bryn Jackson's 2015 article named it. The reason it is 8 and not 10: most common screen
resolutions divide evenly by 8, so layouts render without half-pixel blurring across 1×/1.5×/2×/3×
densities, and 8 subdivides cleanly to 4 and 2 when you need a half-step.

## 6. Balance

Visual weight distributed across the composition. Weight comes from size, darkness, saturation,
complexity and isolation — a small dark element can balance a large pale one.

- **Symmetrical** — mirrored around an axis. Formal, stable, traditional, trustworthy. Risks inert.
- **Asymmetrical** — different elements balanced by weight rather than mirroring. Dynamic, modern,
  more interesting, harder to get right.
- **Radial** — elements arranged around a central point. Draws the eye hard to the centre; strong
  for a single dominant subject.

Judging balance takes a trained eye, and it is closely tied to how white space is distributed (§3),
not just where the objects are. Practical test: blur the design until you cannot read it, and see
where the mass sits.

## 7. Movement

Movement is how you control the *order* in which things are seen — hierarchy (`principles.md` §4)
decides what matters, movement decides the path between them. Four levers:

- **Rhythm and repetition** — repeated elements create a beat the eye follows (`gestalt.md` §1).
- **Colour and contrast** — the eye goes to the highest-contrast point first, then the next.
- **Leading lines and perspective** — real or implied lines that point; converging perspective is the
  strongest version.
- **Implied action** — a figure looking or moving in a direction pulls the eye that way. Gaze
  direction is remarkably strong; a subject looking off-frame leaks attention out of the design.

For reading paths specifically — F-pattern, Z-pattern and the rest — see `gestalt.md` §2, which
carries the evidence and, importantly, the conditions under which each actually applies.
