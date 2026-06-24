#!/usr/bin/env python3
"""Validate an authored test-case CSV is ready to hand off to the testcase-importer skill.

Checks the canonical columns/order, the controlled vocab, unique IDs, and that authored
content (Title/Steps/Expected/Severity_Reasoning) is actually filled — because this skill
AUTHORS cases (unlike the importer, which infers gaps), so blanks here mean unfinished work.

Usage:  python validate_cases.py <cases.csv>
Exit 0 = importer-ready; exit 1 = problems (printed).
"""
import csv, sys, collections

CANON = ["ID", "Group", "Type", "Outcome", "Priority", "Severity_Reasoning",
         "Transition", "Title", "Steps / Test Data",
         "Expected Result + Downstream Impact / Fix"]
VOCAB = {"Type": {"POS", "NEG", "VAPT"},
         "Outcome": {"TN", "TP", "FP", "FN!"},
         "Priority": {"P0", "P1", "P2", "CRIT", "HIGH", "MED", "LOW"}}
REQUIRED = ["Title", "Steps / Test Data", "Expected Result + Downstream Impact / Fix",
            "Severity_Reasoning", "Transition"]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python validate_cases.py <cases.csv>")
    path = sys.argv[1]
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    problems, warnings = [], []

    hdr = list(rows[0].keys()) if rows else []
    if hdr != CANON:
        problems.append(f"columns must be exactly, in order:\n    {CANON}\n  got:\n    {hdr}")
        # can't reliably check the rest if header is wrong
        report(path, len(rows), problems, warnings)
        sys.exit(1)
    if not rows:
        problems.append("no data rows")

    ids = [r["ID"].strip() for r in rows]
    for i, r in enumerate(rows, 1):
        rid = r["ID"].strip() or f"(row {i})"
        if not r["ID"].strip():
            problems.append(f"row {i}: blank ID")
        for col, ok in VOCAB.items():
            v = r[col].strip()
            if v not in ok:
                problems.append(f"{rid}: {col}={v!r} not in {sorted(ok)}")
        # VAPT cases use the CRIT/HIGH/MED/LOW scale; functional use P0/P1/P2
        # Scale convention is advisory: testcase-importer normalizes priority-to-scale on
        # import, so a mismatch here is a style note, not a blocker.
        t, p = r["Type"].strip(), r["Priority"].strip()
        if t == "VAPT" and p in {"P0", "P1", "P2"}:
            warnings.append(f"{rid}: VAPT case usually uses CRIT/HIGH/MED/LOW, not {p}")
        if t in {"POS", "NEG"} and p in {"CRIT", "HIGH", "MED", "LOW"}:
            warnings.append(f"{rid}: functional case usually uses P0/P1/P2, not {p}")
        for col in REQUIRED:
            if not r[col].strip():
                problems.append(f"{rid}: {col} is blank (author it; this skill doesn't leave gaps)")

    dupes = [i for i, n in collections.Counter(ids).items() if i and n > 1]
    if dupes:
        problems.append(f"duplicate IDs: {dupes}")

    report(path, len(rows), problems, warnings)
    sys.exit(1 if problems else 0)


def report(path, n, problems, warnings):
    print(f"{path}: {n} rows")
    if not problems:
        print("OK — canonical columns, vocab valid, IDs unique, content filled. Importer-ready.")
    else:
        print(f"NOT importer-ready — {len(problems)} problem(s):")
        for p in problems[:50]:
            print("  -", p)
        if len(problems) > 50:
            print(f"  … and {len(problems) - 50} more")
    if warnings:
        print(f"{len(warnings)} style warning(s) (non-blocking; importer will normalize):")
        for w in warnings[:15]:
            print("  ~", w)
        if len(warnings) > 15:
            print(f"  … and {len(warnings) - 15} more")


if __name__ == "__main__":
    main()
