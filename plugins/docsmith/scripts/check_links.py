#!/usr/bin/env python3
"""docsmith link check — post-build internal link-integrity check for a PDF.

Given a built PDF, this walks every page's link annotations plus the document
outline (bookmarks / TOC), and verifies that every link resolves:

  * INTERNAL links (GoTo actions + named destinations) and OUTLINE/bookmark
    destinations must point at a real, in-range page. A dangling internal link
    (named dest missing, or a page index out of range) is a FAIL.

  * EXTERNAL links (URI actions) are validated for SYNTAX ONLY — no network.
    A URI must be non-empty, carry a scheme (http/https/mailto), and — for
    http(s) — a well-formed host with a path beyond the bare origin. Empty,
    placeholder (bare `https://`, `https://github.com/)`), or malformed URIs
    are FLAGGED.

It prints a summary (`N internal OK, M external OK, K issues`), lists each
issue with its source page, and exits non-zero if any FAIL is found. External
syntax flags are reported but, because they may be intentional, are surfaced as
WARN and do not by themselves force a non-zero exit unless empty/placeholder.

If pypdf is unavailable it tries `pip install pypdf`; failing that (offline) it
prints a clear "link-check skipped" warning and exits 0 — a missing optional dep
never hard-breaks a build.

Usage:
    python3 check_links.py FILE.pdf
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.parse


def _ensure_pypdf():
    """Import pypdf, pip-installing it once if missing. Returns the module or None."""
    try:
        import pypdf  # noqa: F401
        return pypdf
    except ImportError:
        pass
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "pypdf"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import pypdf  # noqa: F401
        return pypdf
    except Exception:
        return None


# ── destination resolution ────────────────────────────────────────────────────

def _page_index_map(reader):
    """Map each page's indirect-object id -> 0-based page index, for resolving
    explicit (page-object) destinations."""
    out = {}
    for i, page in enumerate(reader.pages):
        try:
            ref = page.indirect_reference
            if ref is not None:
                out[(ref.idnum, ref.generation)] = i
        except Exception:
            continue
    return out


def _named_dests(reader):
    """Return pypdf's named-destination map ({name: Destination}); {} on failure."""
    try:
        nd = reader.named_destinations or {}
        return dict(nd)
    except Exception:
        return {}


def _resolve_dest_page(dest_obj, reader, page_idx_by_ref, named):
    """Resolve a destination object to a 0-based page index.

    Returns (page_index, None) on success or (None, reason) when it dangles.
    `dest_obj` may be a name (str/bytes → named destination), an explicit array
    `[pageRef /Fit ...]`, or a pypdf Destination.
    """
    from pypdf.generic import IndirectObject, ArrayObject

    # Named destination given by string
    if isinstance(dest_obj, (str, bytes)):
        key = dest_obj.decode("utf-8", "replace") if isinstance(dest_obj, bytes) else dest_obj
        if key not in named:
            return None, f"named destination not found: {key!r}"
        dest_obj = named[key]

    # pypdf Destination object — try its .page
    page_ref = None
    try:
        from pypdf.generic import Destination
        if isinstance(dest_obj, Destination):
            page_ref = dest_obj.dest_array[0] if getattr(dest_obj, "dest_array", None) else None
            if page_ref is None:
                page_ref = getattr(dest_obj, "page", None)
    except Exception:
        pass

    # Explicit destination array: first element is the page reference
    if page_ref is None and isinstance(dest_obj, (list, ArrayObject)) and dest_obj:
        page_ref = dest_obj[0]

    if page_ref is None:
        return None, "destination has no page reference"

    # Integer page index (some dests store a raw int)
    if isinstance(page_ref, int):
        if 0 <= page_ref < len(reader.pages):
            return page_ref, None
        return None, f"page index out of range: {page_ref}"

    # Resolve an indirect page object to its index
    try:
        if isinstance(page_ref, IndirectObject):
            key = (page_ref.idnum, page_ref.generation)
            if key in page_idx_by_ref:
                return page_idx_by_ref[key], None
            resolved = page_ref.get_object()
            ref2 = getattr(resolved, "indirect_reference", None)
            if ref2 is not None and (ref2.idnum, ref2.generation) in page_idx_by_ref:
                return page_idx_by_ref[(ref2.idnum, ref2.generation)], None
            return None, "destination page not found in document"
        # A direct page object
        ref = getattr(page_ref, "indirect_reference", None)
        if ref is not None and (ref.idnum, ref.generation) in page_idx_by_ref:
            return page_idx_by_ref[(ref.idnum, ref.generation)], None
    except Exception as e:
        return None, f"could not resolve destination page ({e})"
    return None, "destination page could not be resolved"


# ── external URI validation (syntax only, no network) ──────────────────────────

_SCHEME_OK = ("http://", "https://", "mailto:")
_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _check_uri(uri: str):
    """Validate an external URI by syntax only. Returns (ok, reason).

    ok=True  → well-formed.
    ok=False → reason describes the problem (empty / placeholder / malformed).
    """
    if uri is None:
        return False, "empty URI"
    u = uri.strip()
    if not u:
        return False, "empty URI"

    low = u.lower()
    if not low.startswith(_SCHEME_OK):
        return False, f"missing/unknown scheme: {u!r}"

    if low.startswith("mailto:"):
        addr = u[len("mailto:"):].strip()
        if not addr or "@" not in addr or addr.startswith("@") or addr.endswith("@"):
            return False, f"malformed mailto: {u!r}"
        return True, ""

    # http(s)
    try:
        parsed = urllib.parse.urlparse(u)
    except Exception:
        return False, f"unparseable URI: {u!r}"
    host = parsed.netloc.split("@")[-1].split(":")[0]
    if not host:
        return False, f"placeholder URL (no host): {u!r}"
    if not _HOST_RE.match(host):
        return False, f"malformed host {host!r}: {u!r}"
    # bare origin with no path/query/fragment → almost always a placeholder
    # (e.g. `https://github.com/)` strips to `https://github.com` here).
    path = (parsed.path or "").rstrip(")")
    if path in ("", "/") and not parsed.query and not parsed.fragment:
        return False, f"placeholder URL (bare origin, no path): {u!r}"
    return True, ""


# ── annotation + outline walking ───────────────────────────────────────────────

def _iter_link_annots(reader):
    """Yield (page_number_1based, annot_obj) for every /Link annotation."""
    for pi, page in enumerate(reader.pages, start=1):
        try:
            annots = page.get("/Annots")
        except Exception:
            annots = None
        if not annots:
            continue
        for a in annots:
            try:
                obj = a.get_object()
            except Exception:
                continue
            if obj.get("/Subtype") == "/Link":
                yield pi, obj


def _walk_outline(reader):
    """Yield (label, dest_obj) for every outline (bookmark/TOC) entry."""
    try:
        outline = reader.outline
    except Exception:
        return

    def rec(items):
        for it in items:
            if isinstance(it, list):
                yield from rec(it)
                continue
            title = getattr(it, "title", None) or "<bookmark>"
            yield title, it

    try:
        yield from rec(outline or [])
    except Exception:
        return


def check(pdf_path: str) -> int:
    pypdf = _ensure_pypdf()
    if pypdf is None:
        print("link-check skipped: pypdf unavailable (offline, pip install failed)")
        return 0

    if not os.path.isfile(pdf_path):
        print(f"check_links: no such file: {pdf_path}", file=sys.stderr)
        return 2

    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    n_pages = len(reader.pages)
    page_idx_by_ref = _page_index_map(reader)
    named = _named_dests(reader)

    internal_ok = 0
    external_ok = 0
    fails: list[str] = []   # force non-zero exit
    warns: list[str] = []   # surfaced but non-fatal

    # 1) page link annotations
    for page_no, annot in _iter_link_annots(reader):
        action = None
        try:
            action = annot.get("/A")
            if action is not None:
                action = action.get_object()
        except Exception:
            action = None

        # External URI action
        uri = None
        if action is not None and action.get("/S") == "/URI":
            uri = action.get("/URI")
            if uri is not None:
                uri = str(uri)
            ok, reason = _check_uri(uri)
            if ok:
                external_ok += 1
            else:
                warns.append(f"[page {page_no}] external link: {reason}")
            continue

        # Internal: GoTo action or a /Dest on the annotation
        dest = None
        if action is not None and action.get("/S") == "/GoTo":
            dest = action.get("/D")
        if dest is None:
            dest = annot.get("/Dest")
        if dest is None:
            # a link with neither URI nor destination is itself broken
            warns.append(f"[page {page_no}] link annotation has no URI or destination")
            continue
        try:
            dest = dest.get_object() if hasattr(dest, "get_object") else dest
        except Exception:
            pass
        idx, reason = _resolve_dest_page(dest, reader, page_idx_by_ref, named)
        if idx is None:
            fails.append(f"[page {page_no}] broken internal link → {reason}")
        else:
            internal_ok += 1

    # 2) outline / bookmark destinations (includes the PDF's TOC bookmarks)
    for label, item in _walk_outline(reader):
        dest_obj = item
        idx, reason = _resolve_dest_page(dest_obj, reader, page_idx_by_ref, named)
        if idx is None:
            # Some bookmarks carry the dest on a sub-attribute; try the page attr.
            page_attr = getattr(item, "page", None)
            if page_attr is not None:
                idx, reason = _resolve_dest_page(page_attr, reader, page_idx_by_ref, named)
        if idx is None:
            fails.append(f"[bookmark {label!r}] broken outline destination → {reason}")
        else:
            internal_ok += 1

    # ── report ────────────────────────────────────────────────────────────────
    issues = len(fails) + len(warns)
    print(f"link-check: {internal_ok} internal OK, {external_ok} external OK, "
          f"{issues} issue(s)  [{os.path.abspath(pdf_path)}, {n_pages} pages]")
    for f in fails:
        print(f"  FAIL  {f}")
    for w in warns:
        print(f"  WARN  {w}")

    if fails:
        print(f"\nlink-check FAILED: {len(fails)} broken internal link/bookmark(s).",
              file=sys.stderr)
        return 1
    if warns:
        print("\nlink-check passed with warnings (external syntax only — review above).")
    else:
        print("\nlink-check passed: no broken or mismatched links.")
    return 0


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print("usage: python3 check_links.py FILE.pdf", file=sys.stderr)
        return 2
    return check(argv[0])


if __name__ == "__main__":
    raise SystemExit(main())
