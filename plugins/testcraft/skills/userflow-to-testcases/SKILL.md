---
name: userflow-to-testcases
description: >
  Author a complete test-case suite FROM a user-flow or feature document — a PDF (preferred),
  markdown, doc, text, or screenshots of an app's flows — and output an importer-ready CSV.
  Models the flow as state machines (actor + resource), then writes cases per transition with
  cross-flow downstream impact, a matrix, end-to-end journeys, and a security/abuse (VAPT) pass;
  tags each case Type (POS/NEG/VAPT), Outcome (TN/TP/FP/FN!) and Priority with severity
  reasoning. Its CSV feeds testcase-importer (flow → CSV → console). Use whenever someone has a
  flow/spec/guide and wants QA test cases GENERATED from it — e.g. "write test cases from this
  user-flow PDF", "generate a test suite from this feature spec", "cover this checkout/onboarding
  flow end to end", "model the states in this flow and test them". Do NOT use to import/reformat
  EXISTING test cases (that's testcase-importer), to generate code-level unit/integration tests
  (pytest/jest), to create test fixtures or seed data, or to render/edit the console.
---

# userflow-to-testcases

Turn a document that describes **how an app works** into a thorough, importer-ready test-case
CSV. This skill **authors new cases** from a flow; its sibling `testcase-importer` **imports
existing** cases. They chain: `flow → [this skill] → cases CSV → [testcase-importer] → console`.

The authoring method (state modeling, per-transition cases, matrix, E2E, VAPT, the tag
taxonomy, severity rules, ID scheme, and the importer-ready output schema) lives in
`references/methodology.md`. **Read it before authoring** — it's the heart of this skill.

## Workflow

### 1 — Read the source
Read the flow document in full. The `Read` tool renders PDFs (preferred input), images, and
markdown/text. Understand every flow, screen, and state transition described, plus the concrete
data shown (IDs, amounts, formats) — you'll reuse real values, never fabricate.

### 2 — Model the states
Per `references/methodology.md` §1: extract the actor/account machine and the resource machine,
code the states, and map each flow/step to a transition. Where the document is ambiguous (what
does "inactive" mean? what deactivates a resource? is zero-balance distinct?), pick the most
defensible reading, **note it as an assumption**, and keep a running list of open questions —
you can't ask the user mid-run.

### 3 — Author comprehensively
Following `references/methodology.md` §2–6, write:
- per-transition cases (happy / negative / edge), each stating its **downstream impact**;
- the **actor×resource matrix** gates (`MX-…`);
- **teardown/deactivation** triggers (`DEACT-…`);
- **end-to-end journeys** (`E2E-…`);
- a **security/abuse (VAPT) pass** (`PT-…`) over the surfaces the flow exposes.

Tag every case (Type / Outcome / Priority) and write a one-sentence Severity_Reasoning, using
the taxonomy and confirmed conventions in §7–8.

### 4 — Write the CSV
Write a CSV with the canonical columns **exactly**, in order (so the handoff to
testcase-importer is clean):
```
ID,Group,Type,Outcome,Priority,Severity_Reasoning,Transition,Title,Steps / Test Data,Expected Result + Downstream Impact / Fix
```
Generate per-Group IDs (`AC-01`, `TU-01`, `MX-…`, `E2E-…`, `PT-…`). Default name:
`<subject>-testcases.csv`.

### 5 — Validate it's importer-ready
```bash
python scripts/validate_cases.py <subject>-testcases.csv
```
Fix anything it flags (wrong columns, out-of-vocab tags, blank authored fields, duplicate IDs,
wrong priority scale for VAPT vs functional) and re-run until it prints "Importer-ready".

### 6 — Write the flow-notes sidecar
Create `<subject>-flow-notes.md`: the state models you assumed, the assumptions you made for
ambiguous points, and the open questions / `⚠` unspecified behaviors a human should confirm.

### 7 — Hand off
Tell the user the CSV is ready and the next step is the **testcase-importer** skill, which will
normalize/validate it and render the offline HTML console (this skill stops at the CSV by
design). Report: case counts by section and by Outcome (highlight `FN!`), the assumptions you
made, and the open questions.

## Examples

**Example 1 — PDF user guide**
Input: `travel-card-guide.pdf` (how register → activate → top-up → redeem works).
→ model actor (none→unverified→active→suspended) + card (not-found→inactive→active-empty→
active-funded→deactivated) → author transitions + matrix + E2E + VAPT → write
`travel-card-testcases.csv` → validate → hand off to testcase-importer.

**Example 2 — feature spec in markdown**
Input: a checkout feature spec. → model cart/order + account states → author cases incl.
coupon/payment/VAPT (amount tampering, IDOR) → CSV → validate → hand off.

**Example 3 — flow described in chat**
The user pastes/refers to a flow. → same pipeline; save the flow to a file if needed, author,
validate, hand off.

## Notes
- **Comprehensive by default**: model every reachable transition and the matrix, not just happy
  paths — the cross-flow `FN!` gaps are the high-value cases.
- **Authoring, not guessing data**: reuse real IDs/amounts/formats from the source; never invent
  test content. If the source lacks a detail, note it in flow-notes rather than fabricating.
- **VAPT is defensive**: write abuse *test cases* (attack input → risk → fix), never working
  exploits, and only for the user's own / authorized app.
- **Stops at the CSV**: rendering the console is testcase-importer's job — keep the separation.
