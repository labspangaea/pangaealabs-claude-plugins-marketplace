# Design principles — the cross-cutting index

> **This file is deliberately short.** Contrast, hierarchy and repetition are each *operationalised*
> in another file — restating them here in full would give you two slightly different answers to the
> same question. Each section below states the principle once and points at where the work happens.

## 1. The four that recur

Robin Williams' **CRAP** is the compact mnemonic for the principles that show up in every critique:
**C**ontrast, **R**epetition, **A**lignment, **P**roximity. Where each one lives:

| Principle | Where it is operationalised |
|---|---|
| **Contrast** | `color.md` §8 (the measurable floor) · `typography.md` §3 (pairing) · §3 below |
| **Repetition** | `gestalt.md` §1 (similarity — the perceptual mechanism) · §5 below |
| **Alignment** | `layout.md` §4 |
| **Proximity** | `gestalt.md` §3 |

## 2. KISS — keep it short and simple

Simple, functional, understood without effort, free of visual distraction. In practice it means four
commitments: **high-quality assets** (a low-resolution photo or a clumsy illustration undoes
everything else), a **precisely chosen typeface** rather than a nearly-right one, **copy that is on
point**, and the discipline to remove anything not doing a job.

The perceptual basis is Prägnanz (`gestalt.md` §8): the eye resolves whatever you give it into the
simplest available reading, so complexity you did not intend to communicate is not received anyway.
The practical consequence is more white space (`layout.md` §3).

This generalises well beyond graphic design — product design, UI/UX and web all inherit it
unchanged.

## 3. Contrast

A **significant** difference between elements — significant being the operative word, since a small
difference reads as a mistake rather than as a decision. Contrast creates impact, signals importance,
and holds interest.

Available channels: colour, value, size, shape, weight, texture, direction, and space.

Two jobs, and they are separate. **Communication** — contrast is what makes the important thing look
important. And **legibility** — without enough of it the message simply is not read, which is a hard
measurable constraint, not a matter of taste. See `color.md` §8 for the WCAG floor.

## 4. Visual hierarchy

Arrange elements so the eye receives them in order of importance: the most important thing first,
then supporting information, then detail. Built from **size and scale**, **colour contrast**, and
**typographic style** — bigger, bolder, higher-contrast reads as more important.

Hierarchy decides *what matters*; movement (`layout.md` §7) decides the *path between* the levels.
The type-scale mechanics are in `typography.md` §4.

The commonest failure is promoting everything: when three things are all the most important, none of
them is. If you cannot name the single most important element in the composition, the viewer cannot
either.

## 5. Repetition and consistency

Reuse the same design elements throughout — shape language, colour palette, texture, gradient, icon
style, spacing rhythm. Repetition is what makes a set of pages read as one system rather than as
several unrelated designs, and it is what lets a viewer learn your visual language once and apply it
everywhere after.

It is also the source of rhythm, which drives movement (`layout.md` §7). The perceptual mechanism is
similarity (`gestalt.md` §1).

## 6. The review checklist

A compact summary of what to check, mapping directly onto the review pass in `SKILL.md`:

1. **Contrast** — is the important thing visibly different? Is text legible? (§3)
2. **Balance** — is visual weight distributed deliberately? (`layout.md` §6)
3. **Visual hierarchy** — can you name the single most important element? (§4)
4. **Headline** — does it carry the message, and is it the most prominent thing? (`typography.md` §2)
5. **Body copy** — is the measure, leading and rag comfortable? (`typography.md` §5–6)
6. **Font** — 2–3 faces maximum, paired with real contrast and a shared mood? (`typography.md` §3)
7. **Colour palette** — a recognisable scheme, deliberately proportioned? (`color.md` §2–3)
