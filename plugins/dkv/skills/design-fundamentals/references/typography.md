# Typography

> Vocabulary, the typeface categories and their permitted roles, pairing, scale, the measurable
> readability numbers, and the anti-pattern list.
>
> Unmarked statements are ordinary craft convention. **⚠ contested** marks something widely repeated
> but weakly supported. Citations appear wherever a specific number is doing the work.

## 1. The vocabulary

Get the terms right first, so the technical feedback later has something to attach to. You cannot
critique type without naming what is wrong, and most type problems are spacing problems.

### Typeface vs font

**"Arial", with all its variations, is the typeface. "Arial Bold" or "Arial Narrow" is a font** — one
specific cut of it. Casual usage treats these as synonyms; the distinction matters the moment you
give an instruction, because "use two fonts" and "use two typefaces" mean very different things.
Bold and Light of one typeface are two fonts but one voice — which is exactly why the 2–3 limit in
§6 counts *typefaces*, and why weight contrast (§3) is effectively free.

### The three spacings

Confusing these is the most common source of vague type feedback, so keep them separate:

| Term | Space between | Applies to | Fix it when |
|---|---|---|---|
| **Kerning** | two *specific* adjacent letters | individual pairs | a gap is visibly uneven — usually in headlines |
| **Tracking** | all letters in a *run*, uniformly | a word, line or block | the whole run is too tight or too airy |
| **Leading** | *baselines*, vertically | lines of a paragraph | lines collide or drift apart (§5) |

Kerning and tracking are both horizontal, which is why they get swapped; the distinction is
*specific pair* versus *whole run*, and **tracking is not a fix for bad kerning**. Bad kerning shows
up at large sizes where the gaps are visible — `AV`, `To`, `Wa`, and anything beside a capital `T`
are the usual offenders. **Metrics kerning** uses the pairs the type designer shipped with the font;
**optical kerning** ignores those and spaces by letterform shape — metrics is right for a well-made
font used normally, optical earns its keep at display sizes and when mixing faces.

Practical tracking notes: loosen slightly for all-caps and for small text, tighten slightly for
large display text so headlines hold together.

### Width

**Condensed → normal → extended.** A width class is a genuinely different cut of the typeface, drawn
with the stroke weights corrected for the new proportions.

This is the section that makes the never-stretch rule in §6 make sense: if you need narrower type,
there is a condensed cut for that, and it was drawn properly. Scaling normal-width type horizontally
gets you the same footprint with the letterforms wrecked.

Condensed buys you more characters per line — useful for headlines that must fit, and for tight
columns. Extended reads as deliberate and spacious, and gets unreadable fast over long runs.

### Weight

**Light → regular → bold → bolder/black.** The cheapest source of hierarchy you have, since it costs
you no additional typeface (see the typeface/font distinction above). Contrast in weight is also the
safest pairing technique in §3.

### Roles

Type in a layout is assigned by role, in descending prominence:

**headline → subheadline → body copy → caption**

Every choice above — size, weight, width, spacing, and the category in §2 — is really the question
"which role is this, and does it look like that role?" A caption set like a headline, or a headline
that does not outrank its subhead, is a hierarchy failure (`principles.md` §4) before it is a
typography one.

### Also worth naming

- **x-height** — height of the lowercase `x`. The single most useful number when pairing faces: two
  typefaces with very different x-heights at the same point size look like different sizes, which
  reads as a mistake rather than as contrast.
- **Baseline** — the invisible line letters sit on; the thing a baseline grid aligns (`layout.md` §5).
- **Measure** — line length, in characters. See §5.

## 2. The six categories

Each category carries a character, and — the part that actually constrains you — each has roles it
can and cannot hold. A face that is illegible at 10pt is not a body face, however beautiful.

| Category | Character | Usable for |
|---|---|---|
| **Serif** | traditional, established, editorial, vintage | headline, subhead, **body** |
| **Sans-serif** | simple, modern, neutral | everything |
| **Script** | elegant, romantic, expressive, creative | **headline only** |
| **Handwritten** | casual, personal, warm, human | everything |
| **Monospace** | structural, technical, retro, precise | everything |
| **Display** | decorative, loud, characterful | **headline only** |

Script and display are headline-only for the same reason: they buy personality by sacrificing
legibility at small sizes and over long runs. Using them for body copy spends the personality on
text nobody can comfortably read.

## 3. Pairing

The standard move is **two faces from different categories** — that is where dynamic contrast comes
from. But not every pair works, and the two governing axes are:

- **Contrast** — the faces must be clearly different. Two similar sans-serifs read as one font used
  inconsistently, i.e. as a mistake. Boring is the failure mode here.
- **Balance** — they must still belong to the same message. Push contrast too far and the pairing
  becomes the subject; the reader notices the typography instead of the content.

Techniques that reliably produce both:

1. **Weight contrast within one family** — Extra Bold headline over Light body. Safest possible
   pairing, and a superfamily (a serif and sans built together) is the safest version of that.
2. **Same category, different tracking and size** — the contrast comes from treatment, not face.
3. **Mood pairing** — pick both faces to serve one mood (retro, luxury, playful, romantic) and let
   the mood adjudicate. This is the technique that scales to expressive work.

Worked examples, all display-plus-script pairings of the third kind:

| Headline | Partner | Mood |
|---|---|---|
| Montserrat Extra Bold | Monsieur La Doulaise | modern weight against formal calligraphy |
| Railroad Gothic ATF Black | Third Rail | condensed industrial |
| Fields Extra Bold | Violetta | bold display against delicate script |
| Beautique Display Bold | Classique Script | editorial luxury |

Two caveats worth stating outright: font pairing depends heavily on taste and
accumulated experience, and **matching x-heights matters more than matching names**. When a pairing
feels subtly wrong and you cannot say why, compare x-heights first.

## 4. Scale and hierarchy

Sizes should come from a **modular scale**: pick a base size and a ratio, then multiply and divide
to generate every other size. This is what makes a type system feel deliberate — the sizes are
visibly related rather than arbitrary.

Common ratios, smallest contrast first:

| Ratio | Name | Character |
|---|---|---|
| 1.125 | major second | very tight; dense UI |
| 1.200 | minor third | conservative, workhorse |
| 1.250 | major third | comfortable default |
| 1.333 | perfect fourth | clear, common in editorial |
| 1.500 | perfect fifth | dramatic |
| **1.618** | **golden ratio (φ)** | very dramatic; few steps before it gets unusable |

Worked example at base 16px, ratio 1.25: `16 → 20 → 25 → 31 → 39 → 49`. At φ from 16px:
`16 → 26 → 42 → 68` — only four usable steps, which is why φ suits posters and title slides more
than interfaces.

⚠ **contested — φ as a law of beauty.** The claim that 1.618 governs aesthetic preference traces to
Adolf Zeising in the 1850s, who saw the ratio in places it is not; Keith Devlin and others find no
scientific support for φ driving what people find beautiful, and the famous attributions to the
Parthenon and the Mona Lisa are retrofitted. **φ remains a perfectly good scale ratio — it is simply
one option among several, not the correct one.** Choose your ratio by how much hierarchy contrast the
project needs.

Hierarchy is then built from **size, weight and colour together** — headline, subheadline, body,
caption. Changing only one channel produces weak hierarchy; changing all three at once on every level
produces noise. Two channels per step is usually right.

## 5. Measure and leading

> Both are measurable, and both are where "the spacing looks off" turns into an actual value.

**Measure** (line length) for body text: **45–75 characters per line**, the range established by
Tschichold and Bringhurst, with ~66 the most-cited optimum. On screen, Material Design suggests
40–60. Too long and the eye loses the return sweep to the next line; too short and the rhythm breaks
every few words.

**Leading**: **120–150% of font size** for body text, with ~1.5–1.6 typical for desktop body copy.
The relationship you need to remember is that **measure and leading move together** — a longer
measure needs more leading to keep the eye on the right line. Headlines go tighter (1.0–1.2), because
large type already has plenty of visual space between lines.

## 6. Anti-patterns

The reliable list of what makes type look amateurish:

- **More than 2–3 fonts.** Two is usually right. Weights within a family are free — use those
  instead of reaching for another face.
- **Bad kerning**, especially in headlines where it is visible.
- **Leading too tight or too loose** — lines collide, or the paragraph stops reading as one block.
- **Weak contrast** between hierarchy levels, or between text and background (`color.md` §8).
- **A pairing whose moods disagree** — a playful script over a technical monospace, with no concept
  binding them.
- **A low-readability face on the most important text.** The most common serious error: the headline
  matters most, so it gets the most decorative font, so the thing that mattered most is the hardest
  thing to read.
- **Messy body copy** — a ragged right edge with a lumpy silhouette, **widows** (a lone word or line
  stranded from its paragraph) and **rivers** (vertical channels of white space running down through
  justified text, usually caused by justification with too narrow a measure).
- **Never stretch type.** Horizontal or vertical scaling destroys the stroke-weight relationships the
  designer built. If you need it wider, use a condensed or extended cut of the family.

Frame all of these the right way round: **they are basic rules, and breaking one for a specific
reason is fine.** A critique should name the rule, then ask whether the break is deliberate and
buying something — not just flag the deviation.
