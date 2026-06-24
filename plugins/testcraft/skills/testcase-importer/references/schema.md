# Canonical schema, vocab, and inference rules

The target the importer maps everything onto. The HTML console (`render_console.py`) and
the project tooling read exactly these columns, in this order.

## Columns

| Column | Meaning |
|---|---|
| `ID` | Stable unique key. Kept from source if present; else generated `<PREFIX>-NN` per Group. |
| `Group` | Section / module / flow the case belongs to (e.g. Login, Top-Up, VAPT-Auth). |
| `Type` | What the case feeds — `POS` / `NEG` / `VAPT`. |
| `Outcome` | What a pass proves — `TN` / `TP` / `FP` / `FN!`. |
| `Priority` | Severity. Functional cases: `P0` / `P1` / `P2`. VAPT cases: `CRIT` / `HIGH` / `MED` / `LOW`. |
| `Severity_Reasoning` | One sentence tying the priority to blast radius. |
| `Transition` | State-machine move `From→To` (e.g. `A1→A2`), `A1×C3` matrix cell, or `-` if not state-bound. |
| `Title` | Short case name. |
| `Steps / Test Data` | The action + concrete inputs. |
| `Expected Result + Downstream Impact / Fix` | Expected result; for functional cases also how this state gates a later flow; for VAPT, the recommended fix. |

## Vocab (never drift)

- **Type** — `POS` valid input expecting success · `NEG` invalid input expecting rejection · `VAPT` security/abuse input.
- **Outcome** — what a passing test proves:
  - `TN` good input **correctly allowed** (happy path)
  - `TP` invalid input **correctly blocked** (ordinary validation fires)
  - `FP` legit/edge input must **not** be wrongly rejected
  - `FN!` malicious/invalid input must **not** be wrongly accepted — **security-critical**
- **Priority** — two scales: functional `P0/P1/P2` (blocker/major/minor); VAPT `CRIT/HIGH/MED/LOW`.

## How the script maps (deterministic — for context)

- **Headers** are fuzzy-matched (case/spacing/underscore-insensitive) onto canonical columns.
  Common synonyms: Group←module/feature/section/category/area/flow; Type←pos-neg/kind;
  Priority←severity/sev/criticality/risk; Title←scenario/name/summary; Steps←test steps/input/
  procedure/repro; Expected←result/assertion/acceptance. Unmapped source columns are reported.
- **Values** normalize: positive/valid/happy→`POS`; negative/invalid/error→`NEG`;
  security/pentest/abuse/attack→`VAPT`. true-positive→`TP`, false-negative→`FN!`, etc.
  Severity words/tokens resolve to a tier (critical/p0→0 … low→3) then emit on the scale that
  matches the case's Type (so a functional "High" becomes `P1`, a VAPT "P0" becomes `CRIT`).
- **IDs** kept when present; generated `<PREFIX>-NN` otherwise (PREFIX = initials of Group).

## How to fill gaps (judgment — this is the model's job)

The script leaves a field blank when it can't decide, and lists those rows in the gaps report.
Fill each blank by reasoning from the row's `Title` + `Steps` + `Expected`. Rules:

- **Type** — does the case feed valid input expecting success (`POS`), invalid input expecting a
  graceful reject (`NEG`), or an attack/abuse payload (`VAPT`)? Security/auth/money-tampering/
  injection/IDOR wording ⇒ `VAPT`.
- **Outcome** — combine Type with intent:
  - good input + expects accept → `TN`
  - invalid input + expects reject → `TP` for ordinary validation; **`FN!`** when wrongly accepting
    would breach security/money/ownership/auth (most `VAPT` and money cases)
  - legit edge input that might be wrongly blocked (boundary values, idempotent retries) → `FP`
  - attack input that must be rejected → `FN!`
- **Priority** — by blast radius, on the scale matching Type:
  - `P0` / `CRIT` — money loss, account/data takeover, or blocks an entire flow with no workaround
  - `P1` / `HIGH` — major but narrower or recoverable
  - `P2` / `MED` / `LOW` — cosmetic, edge, low reach
- **Severity_Reasoning** — one sentence naming the blast radius that justifies the priority
  (e.g. "Forged callback credits balance for free."), not a restatement of the title.
- **Transition** — only if the source describes states/preconditions; map to codes (`A1→A2`,
  `C2/C3`, `A1×C3`). Otherwise leave `-`.

## Confirmed conventions (approved defaults — apply, then flag for a glance)

These recurring judgment calls have a settled default. Use it; still note the row in the
review sidecar so the user can override per project.

- **Duplicate value on a uniqueness/identity field** (email already in use, reuse of a
  one-time coupon/token) → `NEG` / **`FN!`**. Wrongly *accepting* it breaches account
  ownership or single-use integrity, which is the `FN!` test even without an attack payload.
  (Downgrade to `TP` only if the team treats it as plain form validation.)
- **Benign empty-state / boundary edges** (no-match search, removing the last cart item,
  amount exactly at a limit) → `POS` / **`FP`**: legit input that must not be misread as an
  error. Usually low priority (`P2`/`MED`).
- **Explicit attack payloads** (injection, tampering, brute force, forged callbacks) →
  `VAPT` / **`FN!`**, on the VAPT priority scale (`CRIT` for takeover/money/data-loss).
- **IDs** — keep the per-Group prefix scheme (`SE-01`, `CA-01`, …); it keeps related cases
  grouped and readable. Do not force a single flat prefix.

## Confidence & flagging

When the wording does **not** clearly imply a field, pick the **most defensible** value and record
it in the review sidecar (`<name>-import-review.md`) as a row needing a human glance, with one line
on why it was uncertain. Never silently guess a security-critical `FN!`/`CRIT` without flagging it.

For **content gaps** (a blank `Title`, `Steps`, or `Expected` — the source itself was incomplete):
do **not** fabricate test content. Leave it blank, flag the row, and tell the user the source was
missing that field.
