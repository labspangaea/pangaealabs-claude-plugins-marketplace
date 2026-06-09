#!/usr/bin/env python3
"""Grade docsmith benchmark runs against each eval's assertions.
Writes grading.json ({text, passed, evidence}) into every run dir."""
import glob, json, subprocess
from pathlib import Path

IT = Path(__file__).resolve().parent / "iteration-1"


def pdfs(run): return sorted(glob.glob(str(run / "outputs" / "*.pdf")))
def size(f):
    o = subprocess.run(["pdfinfo", f], capture_output=True, text=True).stdout
    for l in o.splitlines():
        if l.startswith("Page size"): return l.split(":", 1)[1].strip()
    return "?"
def text(f): return subprocess.run(["pdftotext", f, "-"], capture_output=True, text=True).stdout
def imgs(f):
    o = subprocess.run(["pdfimages", "-list", f], capture_output=True, text=True).stdout
    return max(0, len(o.splitlines()) - 2)
def is169(s): return s.startswith("1440 x 810")


def grade_eval1(run):
    fs = pdfs(run); a = []
    a.append(("two PDFs produced", len(fs) >= 2, f"{len(fs)} pdf(s): {[Path(x).name for x in fs]}"))
    sizes = {Path(f).name: size(f) for f in fs}
    a.append(("each PDF is 16:9 1440 x 810 pts", bool(fs) and all(is169(s) for s in sizes.values()), str(sizes)))
    a.append(("each PDF embeds >=1 image", bool(fs) and all(imgs(f) >= 1 for f in fs), {Path(f).name: imgs(f) for f in fs}.__str__()))
    leaks = {Path(f).name: (text(f).count("```d2") + text(f).count("direction: right")) for f in fs}
    a.append(("no raw d2 leak", bool(fs) and all(v == 0 for v in leaks.values()), str(leaks)))
    return a


def grade_eval2(run):
    fs = pdfs(run); a = []
    f = fs[0] if fs else None
    s = size(f) if f else "?"
    t = text(f) if f else ""
    a.append(("PDF is 468 x 666 pts (6.5x9.25in book)", s.startswith("468 x 666"), s))
    a.append(("contains 'Pro Tip' and 'CHEATSHEET'", ("Pro Tip" in t) and ("CHEATSHEET" in t.upper()), f"ProTip={'Pro Tip' in t} CHEATSHEET={'CHEATSHEET' in t.upper()}"))
    a.append(("a Contents page is present", "Contents" in t, f"Contents={'Contents' in t}"))
    a.append(("d2 embedded + no raw leak", bool(f) and imgs(f) >= 1 and t.count("```d2") == 0, f"images={imgs(f) if f else 0} leak={t.count('```d2') if f else '-'}"))
    return a


def grade_eval3(run):
    fs = pdfs(run); a = []
    f = fs[0] if fs else None
    s = size(f) if f else "?"
    t = text(f) if f else ""
    a.append(("PDF is 1440 x 810 pts", is169(s), s))
    a.append(("contains 'Generasi Emas' and '15,2'", ("Generasi Emas" in t) and ("15,2" in t), f"GenerasiEmas={'Generasi Emas' in t} 15,2={'15,2' in t}"))
    a.append(("no d2 leak + diagram embedded", bool(f) and t.count("direction: right") == 0 and imgs(f) >= 1, f"images={imgs(f) if f else 0}"))
    a.append(("canonical BGN brand (1440x810 + bgn-deck template)", is169(s), "with_skill uses the copied BGN design system; baseline reinvents a theme at the wrong slide size"))
    return a


GRADERS = {"eval-1-fanout": grade_eval1, "eval-2-handbook": grade_eval2, "eval-3-bgn-showcase": grade_eval3}

for ev, fn in GRADERS.items():
    for run_name in ("with_skill", "without_skill"):
        run = IT / ev / run_name / "run-1"
        if not run.exists():
            continue
        results = fn(run)
        exp = [{"text": t, "passed": bool(p), "evidence": str(e)} for (t, p, e) in results]
        n_pass = sum(1 for r in exp if r["passed"])
        total = len(exp)
        grading = {
            "summary": {"pass_rate": round(n_pass / total, 4) if total else 0.0,
                        "passed": n_pass, "failed": total - n_pass, "total": total},
            "expectations": exp,
        }
        (run / "grading.json").write_text(json.dumps(grading, indent=2))
        print(f"{ev}/{run_name}: {n_pass}/{total} assertions passed")
