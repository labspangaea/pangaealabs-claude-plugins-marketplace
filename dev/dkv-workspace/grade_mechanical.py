#!/usr/bin/env python3
"""Mechanical half of the dkv eval grading.

The assertions split cleanly in two: some are countable (did it read >3 reference
files? is there an actual contrast ratio in the text?) and some need a reader
(did it *qualify* the golden-ratio claim, or just omit it?). This does the
countable half so it is consistent across iterations and cheap to re-run; the
judgment half is graded by reading the responses.

Usage: python3 grade_mechanical.py <iteration-dir>
"""
import json
import re
import sys
from pathlib import Path

# ponytail: regex probes, not parsing. These are signals for a human/model reader
# to confirm, not a verdict — a miss here means "go look", not "failed".
PROBES = {
    "hex_values": re.compile(r"#[0-9a-fA-F]{6}\b"),
    # a real measured ratio: "4.5:1", "8.21 : 1" — not a bare "16:9" aspect ratio
    "contrast_ratio": re.compile(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*:\s*1\b"),
    "sixty_thirty_ten": re.compile(r"60\s*[/\-–]\s*30\s*[/\-–]\s*10|60%.{0,40}30%.{0,40}10%", re.S),
    "severity_column": re.compile(r"\|[^|\n]*severity[^|\n]*\|", re.I),
    "wcag": re.compile(r"WCAG|4\.5\s*:\s*1|3\s*:\s*1", re.I),
    "cmyk": re.compile(r"\bCMYK\b", re.I),
    "scale_ratio": re.compile(r"\b1\.(125|2|200|25|250|333|5|500|618)\b"),
}
REF_NAMES = {"color.md", "typography.md", "layout.md", "gestalt.md", "principles.md"}


def grade_run(run_dir: Path) -> dict:
    # two layouts in the wild: <cfg>/outputs/ (iteration-1) and <cfg>/run-N/outputs/
    # (what aggregate_benchmark.py expects). Accept either.
    resp = run_dir / "outputs" / "response.md"
    if not resp.exists():
        nested = sorted(run_dir.glob("run-*/outputs/response.md"))
        if nested:
            resp = nested[0]
    if not resp.exists():
        return {"error": f"no response.md in {run_dir}"}
    run_dir = resp.parent.parent
    text = resp.read_text()

    out: dict = {"words": len(text.split())}
    for name, pat in PROBES.items():
        hits = pat.findall(text)
        out[name] = {"found": bool(hits), "count": len(hits)}

    # contrast ratios are the headline discriminator — keep the actual values
    ratios = [m for m in PROBES["contrast_ratio"].findall(text)]
    # drop aspect-ratio-looking noise (16:1 etc. is implausible as contrast)
    out["contrast_ratio"]["values"] = sorted({r for r in ratios if float(r) <= 21.0})

    # router: how many distinct reference files did it actually open?
    fr = run_dir / "outputs" / "files_read.txt"
    if fr.exists():
        read = {Path(l.strip()).name for l in fr.read_text().splitlines() if l.strip()}
        refs = sorted(read & REF_NAMES)
        out["router"] = {
            "refs_read": refs,
            "n_refs": len(refs),
            "within_budget": len(refs) <= 3,
            "read_skill_md": "SKILL.md" in read,
        }
    else:
        out["router"] = None  # baseline runs have no skill to route through
    return out


def main() -> None:
    root = Path(sys.argv[1])
    report = {}
    for eval_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for cfg in ("with_skill", "without_skill"):
            d = eval_dir / cfg
            if d.exists():
                report[f"{eval_dir.name}/{cfg}"] = grade_run(d)
    print(json.dumps(report, indent=2))
    (root / "mechanical.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
