#!/usr/bin/env python3
"""Programmatic grader for the make-pdf eval.

Usage: python3 grade_run.py <run_dir> <eval_id>
  <run_dir> contains outputs/ (source.md, *.svg, output.pdf) and (optionally) timing.json.
Writes <run_dir>/grading.json in the skill-creator schema (expectations[].{text,passed,evidence} + summary).
All checks are objective; design quality stays a human call in the viewer.
"""
import json, subprocess, sys
from pathlib import Path


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout
    except Exception:
        return ""


def main():
    run_dir = Path(sys.argv[1])
    eval_id = int(sys.argv[2])
    out = run_dir / "outputs"
    pdf, src = out / "output.pdf", out / "source.md"
    src_text = src.read_text(errors="ignore") if src.exists() else ""
    svgs = sorted(out.glob("*.svg"))
    info = sh(["pdfinfo", str(pdf)]) if pdf.exists() else ""
    text = sh(["pdftotext", str(pdf), "-"]) if pdf.exists() else ""
    # whitespace-normalized text: a wrapped cover title ("Choosing a Vector\nDatabase")
    # should still match the contiguous phrase.
    norm = " ".join(text.split())
    pages, pagesize = 0, ""
    for line in info.splitlines():
        if line.startswith("Pages"):
            try: pages = int(line.split(":")[1].strip())
            except ValueError: pass
        if line.startswith("Page size"):
            pagesize = line.split(":", 1)[1].strip()

    exps = []
    def add(t, ok, ev): exps.append({"text": t, "passed": bool(ok), "evidence": ev})

    svg_embed = bool(svgs) and (".svg" in src_text)
    if eval_id == 0:
        add("PDF built successfully (exists, >= 1 page)", pdf.exists() and pages >= 1,
            f"exists={pdf.exists()}, pages={pages}")
        add("Page size is the deck format 1440 x 810 pts", "1440 x 810" in pagesize,
            f"Page size: {pagesize or 'N/A'}")
        add("Authored at least one hand-written .svg and embedded it", svg_embed,
            f"{len(svgs)} svg(s) {[s.name for s in svgs]}; source refs .svg={'.svg' in src_text}")
        has_callout = 'class="callout' in src_text
        add('Source uses at least one <aside class="callout ..."> callout', has_callout,
            "found <aside class=callout>" if has_callout else "no callout aside in source")
        fences = src_text.count("```")
        add("Source contains a fenced code block", fences >= 2, f"``` fence markers: {fences}")
        bg = "![bg" in src_text
        add("Uses an SVG hero image and/or a marp ![bg ...] background", bg or svg_embed,
            f"![bg present={bg}; svg embed={svg_embed}")
        add("Branded 'Pangaea Digital Labs'", "Pangaea" in text,
            "'Pangaea' in PDF text" if "Pangaea" in text else "not found in PDF text")
    elif eval_id == 1:
        add("PDF built successfully (exists, >= 1 page)", pdf.exists() and pages >= 1,
            f"exists={pdf.exists()}, pages={pages}")
        book = ("468" in pagesize and "666" in pagesize) and ("1440 x 810" not in pagesize)
        add("Page size is the handbook book trim (~468 x 666 pts, NOT 1440x810)", book,
            f"Page size: {pagesize or 'N/A'}")
        add("Authored at least one hand-written .svg diagram and embedded it", svg_embed,
            f"{len(svgs)} svg(s); source refs .svg={'.svg' in src_text}")
        leak = text.count("```d2")
        add("No raw ```d2 fence leaked into the PDF text", leak == 0,
            f"'```d2' occurrences in PDF text: {leak}")
        title_ok = "Choosing a Vector Database" in norm
        add("PDF text contains the title 'Choosing a Vector Database'", title_ok,
            "found (whitespace-normalized)" if title_ok else "title not in PDF text")
        add("Document ends with a Glossary", "Glossary" in text,
            "found 'Glossary'" if "Glossary" in text else "no Glossary in PDF text")

    passed = sum(1 for e in exps if e["passed"])
    total = len(exps)
    grading = {"expectations": exps,
               "summary": {"passed": passed, "failed": total - passed, "total": total,
                           "pass_rate": round(passed / total, 4) if total else 0.0}}
    tf = run_dir / "timing.json"
    if tf.exists():
        try:
            t = json.loads(tf.read_text())
            grading["timing"] = {"total_duration_seconds": t.get("total_duration_seconds", 0.0)}
            grading["execution_metrics"] = {"errors_encountered": 0,
                                            "total_tool_calls": 0}
        except json.JSONDecodeError:
            pass
    (run_dir / "grading.json").write_text(json.dumps(grading, indent=2))
    print(f"{run_dir.parent.parent.name}/{run_dir.parent.name}: {passed}/{total} "
          f"({grading['summary']['pass_rate']*100:.0f}%)")


if __name__ == "__main__":
    main()
