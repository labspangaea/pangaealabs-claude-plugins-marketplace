# testcraft

Turn an app's **user flows** into a complete, importer-ready **test-case suite** and a
single-file, offline **HTML console** — then keep it fed as your cases evolve.

![The testcase-importer console — a single-file, offline test matrix: header counters (total / critical / FN!) with an outcome distribution bar, faceted filters (section, outcome, severity, type) plus search, and severity-colored case rows that expand to steps + downstream impact.](assets/console-preview.png)

## The pipeline

```
flow doc (PDF / markdown / spec / screenshots)
    │
    ▼  userflow-to-testcases   — author: state machines → cases → CSV
canonical test-case CSV
    │
    ▼  testcase-importer       — normalize any case data → render
offline HTML console (filter / search / severity, ? opens a legend)
```

## Skills

- **userflow-to-testcases** — authors cases FROM a flow document. Models actor + resource
  state machines, writes per-transition cases with cross-flow **downstream impact**, an
  actor×resource matrix, end-to-end journeys, and a security/abuse (VAPT) pass; outputs an
  importer-ready CSV and a flow-notes sidecar (assumptions + open questions). Stops at the CSV.
- **testcase-importer** — imports/normalizes **existing** case data (xls/xlsx, CSV/TSV, PDF
  tables, pasted/markdown) into the canonical CSV and renders the offline console. Fuzzy-maps
  foreign headers, standardizes the vocab, keeps/generates IDs, infers gaps, flags uncertain ones.

## Agents (subagents)

- **testcase-architect** — heavy / parallel authoring of a full state-machine suite from any
  source (conversation, guide, spec, repo).
- **testcase-vapt-auditor** — adversarial security pass (auth, OTP/secrets, ownership/
  enumeration, credential/PIN, money, IDOR, injection, rate-limit) producing abuse cases with
  recommended fixes. Defensive / authorized-testing use only.

## Canonical schema

The interchange format between the skills and the console — 10 columns, exact order:

```
ID, Group, Type, Outcome, Priority, Severity_Reasoning, Transition,
Title, Steps / Test Data, Expected Result + Downstream Impact / Fix
```

- **Type** `POS` / `NEG` / `VAPT`
- **Outcome** `TN` (good allowed) / `TP` (bad blocked) / `FP` (legit-edge must-not-block) /
  `FN!` (malicious must-not-pass — security-critical)
- **Priority** functional `P0/P1/P2`, VAPT `CRIT/HIGH/MED/LOW`

## Usage

Install the marketplace, then the skills are slash-invocable:

```
/userflow-to-testcases   # author from a flow doc
/testcase-importer       # normalize + render existing cases
```

End-to-end example:

```
"generate a test suite from this onboarding-flow.pdf"   → canonical CSV
"load that CSV into the console"                          → offline HTML console
```

## Dependencies

Python 3. Spreadsheets use `pandas` / `openpyxl`; PDF tables use `pdfplumber` (the importer
degrades with a clear install hint if it's absent). The rendered console is dependency-free
(system fonts, runs from disk).

## Bundled scripts

- `skills/testcase-importer/scripts/normalize_testcases.py` — parse + map + normalize → canonical CSV
- `skills/testcase-importer/scripts/render_console.py` — canonical CSV → offline HTML console
- `skills/userflow-to-testcases/scripts/validate_cases.py` — assert a CSV is importer-ready
