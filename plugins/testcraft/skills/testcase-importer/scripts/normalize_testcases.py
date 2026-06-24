#!/usr/bin/env python3
"""Map arbitrary test-case data (csv / tsv / xls / xlsx / pdf / markdown table)
into the canonical test-case CSV, and report what still needs human/model judgment.

What this script does deterministically:
  - parse the input format into rows
  - fuzzy-match the source headers onto the canonical columns
  - normalize recognized Type / Outcome / Priority values to the canonical vocab
  - keep source IDs when present; generate stable ones (per-group prefix) when missing
  - write the canonical CSV (blank where it could not decide)
  - write a gaps report listing rows that need inference, and what is missing

What it deliberately does NOT do: invent Type / Outcome / Priority / Severity_Reasoning
from the wording of a case. That is judgment — the SKILL.md flow has the model fill the
flagged gaps using the taxonomy, because a rigid keyword script guesses badly and silently.

Usage:
  python normalize_testcases.py INPUT [--name NAME] [--out CSV] [--gaps JSON] [--sheet S]
  INPUT may be '-' to read a markdown/pasted table from stdin.
"""
import csv, json, re, sys, argparse, pathlib

CANON = ["ID", "Group", "Type", "Outcome", "Priority", "Severity_Reasoning",
         "Transition", "Title", "Steps / Test Data",
         "Expected Result + Downstream Impact / Fix"]

# canonical column -> normalized header phrases that should map to it
SYN = {
    "ID":        ["id", "test id", "testcase id", "tc id", "case id", "no", "number", "tc", "ref", "key"],
    "Group":     ["group", "module", "feature", "section", "category", "area", "component",
                  "flow", "epic", "suite", "subsystem"],
    "Type":      ["type", "test type", "case type", "kind", "pos neg", "positivity"],
    "Outcome":   ["outcome", "result class", "classification", "verdict", "class", "tp fp"],
    "Priority":  ["priority", "severity", "sev", "criticality", "importance", "risk", "prio"],
    "Severity_Reasoning": ["severity reasoning", "reasoning", "rationale", "justification",
                  "why", "reason", "risk reason", "severity reason"],
    "Transition": ["transition", "state", "state transition", "from to", "precondition state",
                  "state change", "states"],
    "Title":     ["title", "name", "scenario", "test case", "test scenario", "summary",
                  "case", "objective", "test name"],
    "Steps / Test Data": ["steps", "test steps", "steps test data", "test data", "input",
                  "data", "procedure", "action", "actions", "repro", "reproduction", "how"],
    "Expected Result + Downstream Impact / Fix": ["expected", "expected result", "expected output",
                  "expected behavior", "expected behaviour", "result", "assertion", "acceptance",
                  "downstream", "impact", "fix", "outcome expected", "then"],
}

VALID = {
    "Type": {"POS", "NEG", "VAPT"},
    "Outcome": {"TN", "TP", "FP", "FN!"},
    "Priority": {"P0", "P1", "P2", "CRIT", "HIGH", "MED", "LOW"},
}

TYPE_MAP = {  # normalized value -> canonical
    "pos": "POS", "positive": "POS", "happy": "POS", "valid": "POS", "success": "POS", "+": "POS",
    "neg": "NEG", "negative": "NEG", "invalid": "NEG", "error": "NEG", "failure": "NEG", "sad": "NEG", "-": "NEG",
    "vapt": "VAPT", "security": "VAPT", "sec": "VAPT", "pentest": "VAPT", "pen test": "VAPT",
    "abuse": "VAPT", "attack": "VAPT", "exploit": "VAPT", "vulnerability": "VAPT",
}
OUTCOME_MAP = {
    "tn": "TN", "true negative": "TN", "allow": "TN", "allowed": "TN",
    "tp": "TP", "true positive": "TP", "blocked": "TP", "block": "TP",
    "fp": "FP", "false positive": "FP",
    "fn": "FN!", "fn!": "FN!", "false negative": "FN!",
}
# priority -> severity tier (0 crit .. 3 low)
TIER_MAP = {
    "p0": 0, "0": 0, "critical": 0, "crit": 0, "blocker": 0, "highest": 0, "sev0": 0, "s0": 0,
    "p1": 1, "1": 1, "high": 1, "major": 1, "sev1": 1, "s1": 1,
    "p2": 2, "2": 2, "medium": 2, "med": 2, "minor": 2, "normal": 2, "moderate": 2, "sev2": 2, "s2": 2,
    "p3": 3, "3": 3, "low": 3, "trivial": 3, "lowest": 3, "sev3": 3, "s3": 3,
}
TIER_TO_SCALE = {  # (is_vapt) -> {tier: token}
    True:  {0: "CRIT", 1: "HIGH", 2: "MED", 3: "LOW"},
    False: {0: "P0", 1: "P1", 2: "P2", 3: "P2"},  # functional scale has no LOW
}
INFERABLE = ["Type", "Outcome", "Priority", "Severity_Reasoning", "Transition"]
CONTENT = ["Title", "Steps / Test Data", "Expected Result + Downstream Impact / Fix"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


# ── parsing ────────────────────────────────────────────────────────────────
def parse_markdown(text):
    rows = [ln for ln in text.splitlines() if "|" in ln]
    rows = [r for r in rows if not re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", r)]  # drop --- rule
    out = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        out.append(cells)
    if not out:
        return [], []
    return out[0], out[1:]


def parse_delimited(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.excel
        rdr = list(csv.reader(f, dialect))
    return (rdr[0], rdr[1:]) if rdr else ([], [])


def parse_excel(path, sheet):
    import pandas as pd
    df = pd.read_excel(path, sheet_name=sheet if sheet else 0, dtype=str)
    df = df.where(df.notna(), "")
    return list(df.columns.astype(str)), df.values.tolist()


def parse_pdf(path):
    try:
        import pdfplumber
    except ImportError:
        sys.exit("PDF support needs pdfplumber. Install it:  pip install pdfplumber\n"
                 "(or export the PDF table to CSV/XLSX and re-run).")
    header, body = None, []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables() or []:
                if not tbl:
                    continue
                rows = [[("" if c is None else str(c)).strip() for c in row] for row in tbl]
                if header is None:
                    header, rows = rows[0], rows[1:]
                body.extend(rows)
    if header is None:
        sys.exit("No tables found in the PDF. Export it to CSV/XLSX and re-run.")
    return header, body


def load(path, sheet):
    if path == "-":
        return parse_markdown(sys.stdin.read())
    ext = pathlib.Path(path).suffix.lower()
    if ext in (".csv", ".tsv", ".txt"):
        h, b = parse_delimited(path)
        if len(h) <= 1 and "|" in (h[0] if h else ""):   # a .txt that's really markdown
            return parse_markdown(open(path, encoding="utf-8").read())
        return h, b
    if ext in (".md", ".markdown"):
        return parse_markdown(open(path, encoding="utf-8").read())
    if ext in (".xlsx", ".xls", ".xlsm"):
        return parse_excel(path, sheet)
    if ext == ".pdf":
        return parse_pdf(path)
    # last resort: try markdown then delimited
    txt = open(path, encoding="utf-8").read()
    return parse_markdown(txt) if "|" in txt else parse_delimited(path)


# ── header mapping ─────────────────────────────────────────────────────────
def map_headers(headers):
    """Greedily assign each source column to at most one canonical column."""
    scored = []
    for i, h in enumerate(headers):
        nh = norm(h)
        if not nh:
            continue
        for canon, syns in SYN.items():
            best = 0
            for s in syns:
                if nh == s:
                    best = max(best, 3)
                elif nh.startswith(s) or s.startswith(nh):
                    best = max(best, 2)
                elif s in nh or nh in s:
                    best = max(best, 1)
            if best:
                scored.append((best, -CANON.index(canon), i, canon))
    scored.sort(reverse=True)
    col_of, used_src, used_canon = {}, set(), set()
    for _score, _pri, i, canon in scored:
        if i in used_src or canon in used_canon:
            continue
        col_of[canon] = i
        used_src.add(i)
        used_canon.add(canon)
    mapped_src = used_src
    return col_of, mapped_src


# ── value normalization ────────────────────────────────────────────────────
def norm_type(v):
    nv = norm(v)
    if v.strip().upper() in VALID["Type"]:
        return v.strip().upper()
    return TYPE_MAP.get(nv) or next((t for k, t in TYPE_MAP.items() if k in nv.split()), "")


def norm_outcome(v):
    raw = v.strip().upper().replace(" ", "")
    if raw in VALID["Outcome"]:
        return raw
    nv = norm(v)
    return OUTCOME_MAP.get(nv) or OUTCOME_MAP.get(nv.replace(" ", "")) or ""


def norm_priority(v, is_vapt):
    # Always resolve to a tier then emit on the scale that matches the case type,
    # so a functional case with source "High" becomes P1 (not the VAPT token HIGH),
    # and a VAPT case with source "P0" becomes CRIT. TIER_MAP covers both the canonical
    # tokens (p0/crit/high/...) and plain words (critical/major/medium/...).
    nv = norm(v)
    if not nv:
        return ""
    tier = TIER_MAP.get(nv)
    if tier is None:
        tier = next((t for k, t in TIER_MAP.items() if k in nv.split()), None)
    return TIER_TO_SCALE[is_vapt].get(tier, "") if tier is not None else ""


def group_prefix(group):
    words = re.findall(r"[A-Za-z0-9]+", group)
    if len(words) >= 2:
        return "".join(w[0] for w in words[:3]).upper()
    return words[0][:2].upper() if words else "TC"


# ── main ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="path to csv/tsv/xls/xlsx/pdf/md, or '-' for stdin")
    ap.add_argument("--name", help="output basename (default: from input filename)")
    ap.add_argument("--out", help="canonical CSV path (default: <name>-testcases.csv)")
    ap.add_argument("--gaps", help="gaps report path (default: <name>-import-gaps.json)")
    ap.add_argument("--sheet", help="worksheet name/index for xls/xlsx")
    A = ap.parse_args()

    name = A.name or (re.sub(r"[^A-Za-z0-9._-]+", "-", pathlib.Path(A.input).stem) if A.input != "-" else "imported")
    out_csv = pathlib.Path(A.out) if A.out else pathlib.Path(f"{name}-testcases.csv")
    out_gaps = pathlib.Path(A.gaps) if A.gaps else pathlib.Path(f"{name}-import-gaps.json")

    headers, body = load(A.input, A.sheet)
    if not headers:
        sys.exit("Could not read any header row from the input.")
    col_of, mapped_src = map_headers(headers)
    unmapped = [headers[i] for i in range(len(headers)) if i not in mapped_src and norm(headers[i])]

    def cell(row, canon):
        i = col_of.get(canon)
        return (str(row[i]).strip() if i is not None and i < len(row) else "")

    rows, gaps = [], []
    used_ids, seq = set(), {}
    # first pass: collect explicit IDs to avoid collisions when generating
    for r in body:
        v = cell(r, "ID")
        if v:
            used_ids.add(v)

    for r in body:
        if not any(str(c).strip() for c in r):
            continue
        rec = {c: cell(r, c) for c in CANON}
        rec["Group"] = rec["Group"] or "Imported"
        rec["Type"] = norm_type(rec["Type"])
        rec["Outcome"] = norm_outcome(rec["Outcome"])
        rec["Priority"] = norm_priority(rec["Priority"], rec["Type"] == "VAPT")
        rec["Transition"] = rec["Transition"] or "-"

        if not rec["ID"]:
            pre = group_prefix(rec["Group"])
            n = seq.get(pre, 0) + 1
            cand = f"{pre}-{n:02d}"
            while cand in used_ids:
                n += 1
                cand = f"{pre}-{n:02d}"
            seq[pre] = n
            used_ids.add(cand)
            rec["ID"] = cand

        # Transition legitimately defaults to "-" (not state-bound), so it is not a gap.
        infer = [c for c in INFERABLE if c != "Transition" and not rec[c]]
        content = [c for c in CONTENT if not rec[c]]
        if infer or content:
            gaps.append({"id": rec["ID"], "group": rec["Group"], "title": rec["Title"],
                         "steps": rec["Steps / Test Data"],
                         "expected": rec["Expected Result + Downstream Impact / Fix"],
                         "infer": infer, "content_missing": content})
        rows.append(rec)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CANON)
        w.writeheader()
        w.writerows(rows)

    report = {"name": name, "input": A.input, "rows_total": len(rows),
              "mapped_headers": {c: headers[i] for c, i in col_of.items()},
              "unmapped_source_headers": unmapped,
              "rows_needing_work": gaps}
    out_gaps.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── summary to stdout ──
    miss_count = {c: 0 for c in INFERABLE + CONTENT}
    for g in gaps:
        for c in g["infer"]:
            miss_count[c] += 1
        for c in g["content_missing"]:
            miss_count[c] += 1
    print(f"parsed {len(rows)} rows from {A.input}")
    print(f"mapped columns: {', '.join(c for c in CANON if c in col_of) or '(none — check headers)'}")
    if unmapped:
        print(f"unmapped source columns (dropped): {', '.join(unmapped)}")
    print(f"wrote {out_csv}")
    gappy = [c for c in INFERABLE + CONTENT if miss_count[c]]
    if gappy:
        print(f"gaps to resolve ({len(gaps)} rows): " +
              ", ".join(f"{c}×{miss_count[c]}" for c in gappy))
        print(f"  → infer the blank Type/Outcome/Priority/Severity_Reasoning per the taxonomy,")
        print(f"    then re-validate. Details in {out_gaps}")
    else:
        print("no gaps — CSV is complete and ready to render.")


if __name__ == "__main__":
    main()
