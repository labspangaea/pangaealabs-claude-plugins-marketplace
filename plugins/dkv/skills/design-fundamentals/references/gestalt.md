# Gestalt principles

> The ten grouping laws, each as: what it is → how to use it → how it fails. §11 covers what to do
> when two of them disagree, which is the situation an actual critique has to resolve.

The underlying claim of all of them: the eye groups before it reads. Whatever your layout groups
visually *is* the meaning the viewer receives, regardless of what the content says.

## 1. Similarity

**What** — elements that share a visual attribute are read as belonging together. The attribute can
be colour, shape, size, position, orientation or texture.

**Use it** — give one visual treatment to one class of thing: all links the same colour, all section
headers the same weight, all secondary actions the same button shape. This is what makes an interface
learnable after one exposure.

**Fails when** — two unrelated things share a treatment by accident, and the viewer infers a
relationship that does not exist. The classic version is styling a non-clickable label like a link.
The other failure is over-application: if everything is similar, nothing groups.

Related but distinct: **repetition** as a design principle (`principles.md` §5) is the deliberate
reuse of elements for consistency; similarity is the perceptual law that makes repetition work.

## 2. Continuity

**What** — the eye follows the smoothest available path and prefers continuing in a direction over
changing abruptly — the brain likes smooth, and dislikes sharp turns.

**Use it** — align elements along a line or gentle curve and the eye will travel the whole set as one
group. This is why alignment (`layout.md` §4) does perceptual work and not just tidiness work.

**Fails when** — an accidental line pulls the eye off the intended path, or a break in a line implies
a separation you did not intend.

**Reading patterns.** The named scan patterns are continuity applied to whole pages. Nielsen Norman
Group's 2006 eye-tracking study (232 users) found the **F-pattern**: two horizontal sweeps near the
top, then a vertical scan down the left edge. The condition matters and is usually dropped when the
pattern is repeated:

| Pattern | Applies to |
|---|---|
| **F-pattern** | text-heavy, low-graphic pages |
| **Z-pattern** | image-heavy, low-text pages — landing pages with one clear call to action |
| **Layer-cake** | pages with strong headings; the eye scans headings and skips the prose between |
| **Spotted** | pages being searched for something specific — links, numbers, a name |
| **Commitment** | rare; the reader actually reads the whole thing |

Designing a text-dense page around a Z-pattern, or a single-CTA landing page around an F, is
applying the right principle under the wrong conditions.

## 3. Proximity

**What** — objects near each other are read as a group; objects far apart are read as unrelated.
Proximity typically beats similarity when the two compete.

**Use it** — spacing *is* your grouping mechanism. Put a caption close to its image and far from the
next one; tighten space within a form field's label-and-input pair and loosen it between pairs. You
rarely need a divider line — the space does it.

**Fails when** — spacing is uniform, so nothing groups and the viewer has to work out the structure
from content alone. The other failure is the label that sits equidistant between two fields, which
genuinely reads as ambiguous.

## 4. Figure–ground

**What** — the eye separates a scene into a subject (figure) and everything else (ground), and it
does this before anything else.

**Use it** — make the separation unambiguous through contrast, depth, shadow, blur or opacity. Warm
subject on cool ground (`color.md` §7) is a strong, cheap separation. When the figure and ground are
*deliberately* ambiguous you get **double meaning** — the arrow in the negative space of the FedEx
logo is the canonical example, and the effect works precisely because both readings are stable.

**Fails when** — the separation is unstable by accident: text over a busy photograph with no scrim,
or a subject whose value is too close to its background. If the viewer has to work to find the
subject, they have already stopped looking.

## 5. Common fate

**What** — elements moving in the same direction are grouped, even when far apart and unalike.
Direction, speed and timing all count.

**Use it** — the strongest grouping cue available in motion, so it belongs to animation and interface
transitions: items that animate in together are understood as one set. In static work, *implied*
direction does a weaker version of the same job — arrows, a row of figures all facing one way.

**Fails when** — unrelated things animate in unison and imply a relationship, or related things
animate on different timings and fall out of their group.

## 6. Closure

**What** — given an incomplete shape, the eye supplies the missing parts and perceives the whole.

**Use it** — deliberate gaps make a mark more engaging than a closed one, because completing it is a
small act of participation. This is the mechanism behind most minimal logos built from fragments,
and it lets you imply a form with far fewer elements.

**Fails when** — the gap is too large and the shape does not resolve, so it reads as broken rather
than as implied. The line is genuinely thin, and it is why closure marks need testing at small sizes.

## 7. Symmetry

**What** — symmetrical elements are grouped and read as one stable unit. Three kinds:

- **Reflectional** — mirrored across an axis
- **Rotational** — repeated around a centre point
- **Translational** — repeated by shifting along a direction, producing pattern

**Use it** — symmetry signals order, stability and intent, which is why it dominates in logos,
monograms and formal layouts. Translational symmetry is how you build texture and pattern from one
element.

**Fails when** — symmetry is applied to content that is not actually parallel, forcing unequal things
into equal slots. And perfect symmetry throughout reads as static — see balance, `layout.md` §6.

## 8. Prägnanz (the law of good figure)

**What** — the overarching law the others serve: given anything ambiguous or complex, perception
resolves it into the **simplest, most regular, most stable interpretation available**. Sometimes
called the law of simplicity or good figure.

**Use it** — this is the perceptual justification for KISS (`principles.md` §2). If a simple reading
of your layout exists, that is the reading the viewer will get, whether or not it is the one you
intended. Complexity does not survive contact with a glancing viewer.

**Fails when** — you rely on a subtle or complex reading being noticed. The eye will take the simpler
one. Ask what the *laziest possible* interpretation of your composition is, because that is the one
being received.

## 9. Common region

**What** — elements inside a shared boundary are grouped, even when they are far apart or dissimilar.
The boundary can be a border, a background fill, or a card.

**Use it** — the strongest way to override the other grouping cues. A card with a background fill
groups its contents regardless of their spacing or styling, which is exactly why the card is the
dominant UI pattern.

**Fails when** — you add containers to content that is already grouped by proximity, producing boxes
inside boxes and visual noise. Reach for space first; use a region when space alone cannot carry it.

## 10. Uniform connectedness

**What** — elements joined by a visible connector — a line, a bar, a shared shape — are grouped.
Often the **strongest** grouping cue of all, capable of overriding both proximity and similarity.

**Use it** — connecting lines in diagrams, flowcharts and org charts; a rule that ties a heading to
its section; the bar behind a set of tabs. Note that the connector does not need to touch the
elements for the relationship to register.

**Fails when** — a decorative line accidentally connects two unrelated blocks. Because this cue is so
strong, an accidental connector overrides everything else you did to keep them apart.

## 11. When the principles conflict

Real designs trigger several of these at once, and they do not always agree. The rough order of
strength, most powerful first:

1. **Uniform connectedness** (§10) — a connector beats almost anything
2. **Common region** (§9) — a shared container beats spacing
3. **Proximity** (§3) — space beats appearance
4. **Similarity** (§1) — shared styling is the weakest of the grouping cues

This ordering is the most practically useful thing in this file, because it tells you which lever to
pull. If two elements must read as related but are far apart, styling them alike is the *weakest*
available fix — connect them or contain them instead. And if a grouping in your layout looks wrong
but every element is styled correctly, look for an accidental container or connector overriding your
intent before you touch the styling.
