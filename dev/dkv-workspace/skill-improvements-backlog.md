# dkv — parked skill improvements

Findings from real use, held for a later `/skill-creator:skill-creator` pass. Each carries the
evidence that produced it, because "improve the contrast guidance" is unactionable six weeks from
now and "averaging said 6.61:1, worst patch said 3.09:1, on this file" is not.

Status: **not yet applied.** Ordered by how wrong the skill currently gets the answer.

---

## 1. Text over imagery cannot be measured by averaging — and the skill has no guidance for it

**Severity: high.** This makes the skill produce confidently wrong passes on its own core territory.

`scripts/contrast.py` takes two flat hex colours. Posters, packaging, social posts and thumbnails —
most of what dkv is scoped to — routinely set text directly over photographs and gradients, and the
skill says nothing about how to measure that. Whoever reviews such a piece will sample "the
background", get a single number, and report it.

**Evidence** — reviewing a real tour poster (`780x974-05.jpg`, 3250×4058):

| Text block | Averaged ground | Worst 20px patch | Verdict flips |
|---|---|---|---|
| country list (body, 4.5 floor) | 6.61:1 comfortable pass | `#979736` → **3.09:1** | pass → **fail** |
| `9 NEGARA` (large, 3.0 floor) | 5.67:1 comfortable pass | `#A3A149` → **2.71:1** | pass → **fail** |
| `tripdeals.id` (body) | 18.19:1 | `#1B252B` → 15.6:1 | pass → pass |

The first two sit over water that happens to be dark, with sunlit foliage at one end. Averaged, the
design looks fine. In reality the last two country names are hard to read. A reviewer following the
current skill would have approved it.

**Proposed fix**
- Add an image mode to `contrast.py`: given an image and a text-region box, exclude glyph pixels,
  tile the remaining ground, and report the **worst-case** tile against the applicable floor —
  not the mean.
- Add one line to the review pass §1: *text over photography or gradient is measured at its worst
  patch, never averaged; the average is what makes an unreadable corner look compliant.*

**Trap to encode with it.** The obvious implementation is wrong. Tiling the region and taking the
brightest tile returns the **white letterforms**, not the ground — on the same poster that reported
`#FFFFFF` → 1.0:1 for every block, which is nonsense in the opposite direction. Glyph pixels must be
excluded first (a luminance threshold works when the type is near-white or near-black). Both failure
modes were hit in one sitting; the script should encode the correct method so nobody re-derives it.

---

## 2. The review pass checks absolute floors but never compares peers

**Severity: medium.** Misses a real, common, persuasive-copy defect.

Step 1 asks whether each element clears its floor. Nothing asks whether the *most important* element
is the weakest of its peer group — so a design can pass every check and still bury its own headline
number.

**Evidence** — the same poster's three info chips, all passing:

| Chip | Contrast | Rank |
|---|---|---|
| price `25,9jt` | **3.33:1** | most important |
| duration `13D` | 11.42:1 | supporting |
| dates | 18.32:1 | supporting |

The price is the single most persuasive element and has ~1/5 the contrast of the dates beside it.
Every chip passes; the hierarchy is still inverted.

**Proposed fix** — a line in the review pass, in step 6 (hierarchy) rather than step 1, since it is a
hierarchy fault expressed in contrast: *within a row or group of peer elements, compare the measured
contrast across them. If the most important member is the weakest, the hierarchy is inverted even
though everything passes.*

---

## 3. Smaller: one colour carrying two ranks

**Severity: low.** Probably already covered, worth checking rather than adding.

The poster used the same coral `#EE6160` for the headline band and for the fine-print inclusions
block — similarity groups the loudest and quietest content on the page. Review pass step 5 does ask
"do the visual groups match the meaning?", which arguably catches it, and `gestalt.md` §1 covers
similarity properly. Verify against a case before adding anything; the pass is already long, and an
instruction that duplicates an existing one makes it worse, not better.

---

## How to validate whichever of these gets applied

The poster is a good regression case: it has real failures at real numbers, and both measurement
traps are reproducible on it. Add it as a fourth output-eval case with assertions on the specific
values (`3.13:1` on the coral block, worst-patch `3.09:1` on the country list) rather than on
whether a finding is "mentioned" — the iteration-3 lesson was that vaguely-worded assertions pass
for both configs and discriminate nothing.

Note the triggering eval remains unrunnable without a `claude /login`-authed isolated config; see
the `-INVALID` runs in this directory and the isolation notes in `CLAUDE.md`.
