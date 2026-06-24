---
name: testcase-importer
description: >
  Import and normalize existing test-case data — xls/xlsx, CSV/TSV, PDF tables, or a
  pasted/markdown table — into this project's canonical test-case CSV and render it into the
  offline HTML console. Fuzzy-maps foreign headers onto the schema, standardizes Type
  (POS/NEG/VAPT), Outcome (TN/TP/FP/FN!) and the Priority scales, keeps source IDs (or generates
  them), infers missing tag fields, and flags uncertain ones for review. Use whenever someone has
  test cases in a sheet, CSV, PDF, or table and wants them in the project format or in the console
  — e.g. "convert this QA spreadsheet", "map this test matrix to our format", "normalize this
  testcases xlsx", "turn this PDF of test cases into the CSV", or pasting a table and asking to
  "add these to the matrix". Do NOT use it to author brand-new cases from a feature/flow (that's
  the testcase-architect agent), to import non-test-case data such as a customer or sales CSV into
  a database or chart, to edit/restyle the console, or to query an existing canonical CSV.
---

# Test-case importer

Turn messy, foreign-formatted test-case data into the project's canonical CSV (the 10 columns
the HTML console reads) and render it. The hard parts — parsing odd formats, matching column
names, normalizing vocab, generating IDs, validating — are done by the bundled script. The
judgment part — inferring the tag fields a source didn't provide — is yours, guided by the
taxonomy, because a keyword script guesses those badly and silently.

The canonical schema, vocab, and the rules for inferring missing fields live in
`references/schema.md`. **Read it before filling any gaps.**

## Workflow

### 1 — Locate the input
A file path (`.xlsx`/`.xls`/`.csv`/`.tsv`/`.pdf`/`.md`) or a table pasted into chat. For a
pasted markdown/table, save it to a `.md` file or pipe it via stdin (`... | ... -`).

### 2 — Run the normalizer
```bash
python scripts/normalize_testcases.py <INPUT> --name <NAME>
```
It writes `<NAME>-testcases.csv` (canonical columns, blanks where it couldn't decide) and
`<NAME>-import-gaps.json`, and prints a summary: rows parsed, which columns mapped, which
source columns were **dropped** (unmapped), and which fields still need work.

- PDF needs `pdfplumber` (`pip install pdfplumber`); if absent the script says so — ask the
  user to install it or export the table to CSV/XLSX.
- Old `.xls` uses `xlrd`; `.xlsx` uses `openpyxl`/`pandas` (already available).

### 3 — Read the gaps report and the dropped columns
Open `<NAME>-import-gaps.json`. Two things matter:
- **`unmapped_source_headers`** — columns the script couldn't place. If one clearly holds a
  canonical field the script missed, fix the CSV (or tell the user it was dropped and why).
- **`rows_needing_work`** — each row's blank **inferable** fields (Type/Outcome/Priority/
  Severity_Reasoning) and any **content_missing** fields (Title/Steps/Expected).

### 4 — Fill the inferable gaps (judgment)
For every flagged row, reason from its `Title` + `Steps` + `Expected` and set the blank fields
per `references/schema.md`:
- `Type` POS/NEG/VAPT · `Outcome` TN/TP/FP/FN! · `Priority` on the scale matching Type
  (functional P0/P1/P2, VAPT CRIT/HIGH/MED/LOW) · `Severity_Reasoning` one sentence on blast
  radius · `Transition` only if states are described, else leave `-`.

Edit `<NAME>-testcases.csv` directly to fill the blanks (it's already the right shape). Keep
every value inside the canonical vocab.

**Content gaps** (a blank Title/Steps/Expected — the source was incomplete): do **not**
invent test content. Leave blank, and list the row for the user.

### 5 — Write the review sidecar
Create `<NAME>-import-review.md` listing the rows where you inferred a field that the source
didn't clearly imply (especially any `FN!`/`CRIT` you assigned), one line each on why it's
uncertain, plus any dropped columns and content gaps. This is what the user sanity-checks.

### 6 — Validate and render
```bash
python -c "import csv; rows=list(csv.DictReader(open('<NAME>-testcases.csv'))); \
  assert rows and not [c for c in ['ID','Group','Type','Outcome','Priority','Severity_Reasoning','Transition','Title','Steps / Test Data','Expected Result + Downstream Impact / Fix'] if c not in rows[0]]; print(len(rows),'rows ok')"
python scripts/render_console.py --csv <NAME>-testcases.csv --out <NAME>-testcases.html \
  --title "<Subject> · Test Matrix" --subtitle "<Subject>"
```
Open the HTML to confirm it renders (criticals/FN! show in red, facets populate, `?` opens the
legend).

### 7 — Report
Tell the user: rows imported, columns mapped vs dropped, how many fields you inferred, the
review-sidecar path for the uncertain ones, any content gaps the source was missing, and the
HTML path.

## Examples

**Example 1 — spreadsheet with foreign headers**
Input: `qa_cases.xlsx` with columns `Test ID, Module, Scenario, Steps, Expected, Severity`.
→ run normalizer → it maps those onto ID/Group/Title/Steps/Expected/Priority, leaves
Type/Outcome/Severity_Reasoning blank → infer each from the scenario wording → render.

**Example 2 — pasted markdown table, bare**
Input: a `| Name | Steps | Expected |` table with no tags.
→ save/pipe to normalizer → it maps the three columns and generates IDs → infer
Type/Outcome/Priority/Severity_Reasoning for every row → flag the ones whose intent is
ambiguous in the review sidecar → render.

**Example 3 — already-tagged CSV**
Input: a CSV that already has all ten fields (maybe named differently).
→ normalizer maps and normalizes vocab, reports **no gaps** → validate → render directly.

## Notes
- Never renumber existing IDs; the console and other tooling reference them.
- Color/severity is signal: keep every tag inside the canonical vocab so the console renders it.
- If the source mixes several distinct apps/flows, set `Group` per row so the facets stay useful.
