#!/usr/bin/env python3
"""Remove blank / filler pages from a finished PDF, in place.

The handbook template is a LaTeX `book` class with `openright`, so it inserts
visually blank pages (carrying only a running header + footer + folio, no body)
to make chapters open on a recto, plus an occasional trailing page. Readers
experience these as "empty pages." This strips them.

Detection is **chrome-aware**. A naive character-count threshold fails here:
the running footer (company + author) and the chapter running head add 40-100
characters to *every* page, including the blank ones, so blank pages float above
a fixed threshold and survive. Instead we first discard "chrome" — page furniture
that recurs across the document:

  * folios            -> lines that are only digits / roman numerals
  * running headers   -> a normalized line that appears on >= 2 distinct pages
  * running footers   -> (same recurrence rule; the footer is on every page)

Whatever remains is genuine body text. A page whose remaining body text is below
`--threshold` characters is blank. This is robust to any company name, author, or
chapter title length, because the boilerplate is removed by *recurrence*, not by
guessing its length.

Body text is essentially unique per page, so it is never treated as chrome; figure
pages keep their caption + embedded SVG label text, and chapter-opening pages keep
their first body paragraph, so neither is mistaken for blank.

Safety: page 1 (the cover) is always kept; refuses to drop more than
`--max-fraction` of the document (default 40%); writes to a temp file and moves
over the original only on success; then re-opens the result and *verifies* no
blank pages remain, reporting the outcome.

Usage:
    python3 strip_blank_pages.py FILE.pdf [--threshold 20] [--max-fraction 0.4] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections import Counter

_WS = re.compile(r"\s+")
_ROMAN = re.compile(r"^[ivxlcdm]+$", re.I)
# Running-head furniture: "Chapter 8. ...", "Part II", "Appendix A". Requires a
# number after the keyword so body sentences ("Particularly...") never match.
_HEAD = re.compile(r"^(chapter|part|appendix)\s+[\divxlcdm]", re.I)


def _norm(s: str) -> str:
    return _WS.sub("", s)


def _page_lines(page) -> list[str] | None:
    """Return stripped non-empty lines of a page, or None if it can't be read
    (None => treat as content, never drop)."""
    try:
        text = page.extract_text() or ""
    except Exception:
        return None
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _chrome_lines(pages_lines: list[list[str] | None], recur_cut: int) -> set[str]:
    """Normalized lines that recur on >= recur_cut distinct pages (headers/footers)."""
    counts: Counter[str] = Counter()
    for lines in pages_lines:
        if lines is None:
            continue
        for n in {_norm(ln) for ln in lines if _norm(ln)}:
            counts[n] += 1
    return {ln for ln, c in counts.items() if c >= recur_cut}


def _body_chars(lines: list[str], chrome: set[str]) -> int:
    """Characters left after removing folios and recurring chrome lines."""
    total = 0
    for ln in lines:
        n = _norm(ln)
        if not n:
            continue
        if n.isdigit() or _ROMAN.match(n):   # folio
            continue
        if n in chrome:                       # recurring running header / footer
            continue
        if _HEAD.match(ln.strip()):           # running head of a short chapter
            continue
        total += len(n)
    return total


def blank_pages(reader, threshold: int, keep_first: bool) -> list[int]:
    pages_lines = [_page_lines(p) for p in reader.pages]
    # A header recurs on every page of its chapter; a footer on every page.
    # Require recurrence on >= 2 pages so unique body text is never chrome.
    chrome = _chrome_lines(pages_lines, recur_cut=2)

    drop: list[int] = []
    for i, lines in enumerate(pages_lines, start=1):
        if keep_first and i == 1:
            continue
        if lines is None:                     # unreadable -> keep
            continue
        if _body_chars(lines, chrome) < threshold:
            drop.append(i)
    return drop


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Remove blank/filler pages from a PDF in place.")
    ap.add_argument("pdf", help="path to the PDF to clean")
    ap.add_argument("--threshold", type=int, default=20,
                    help="max body chars (chrome removed) for a page to count as blank (default 20)")
    ap.add_argument("--max-fraction", type=float, default=0.4,
                    help="refuse to drop more than this fraction of pages (default 0.4)")
    ap.add_argument("--keep-first", action="store_true", default=True,
                    help="always keep page 1 (the cover); on by default")
    ap.add_argument("--dry-run", action="store_true", help="report what would be removed, change nothing")
    args = ap.parse_args(argv)

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("strip_blank_pages: pypdf not installed (pip install pypdf)", file=sys.stderr)
        return 2

    if not os.path.isfile(args.pdf):
        print(f"strip_blank_pages: no such file: {args.pdf}", file=sys.stderr)
        return 2

    reader = PdfReader(args.pdf)
    total = len(reader.pages)
    drop = blank_pages(reader, args.threshold, args.keep_first)

    if not drop:
        print(f"OK  no blank pages found ({total} pages)")
        return 0

    if len(drop) > max(1, int(total * args.max_fraction)):
        print(f"REFUSING: {len(drop)}/{total} pages flagged blank exceeds "
              f"--max-fraction {args.max_fraction}; raise --threshold or inspect manually. "
              f"Flagged: {drop}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"DRY-RUN  would remove {len(drop)} blank page(s): {drop} (of {total})")
        return 0

    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i not in drop:
            writer.add_page(page)
    tmp = args.pdf + ".tmp"
    with open(tmp, "wb") as f:
        writer.write(f)
    shutil.move(tmp, args.pdf)

    # Verify: re-open the cleaned file and confirm no blank pages remain.
    verify = PdfReader(args.pdf)
    remaining = blank_pages(verify, args.threshold, args.keep_first)
    kept = len(verify.pages)
    if remaining:
        print(f"WARN  removed {len(drop)} page(s) {drop} -> {kept} pages, "
              f"but {len(remaining)} still look blank: {remaining} : {os.path.abspath(args.pdf)}",
              file=sys.stderr)
        return 1
    print(f"OK  removed {len(drop)} blank page(s) {drop} -> {kept} pages "
          f"(verified 0 blank remaining) : {os.path.abspath(args.pdf)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
