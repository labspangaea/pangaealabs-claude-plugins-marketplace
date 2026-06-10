#!/usr/bin/env python3
"""docsmith shared diagram renderer.

Extract inline ```d2 fenced blocks from a markdown source, render each ONCE to
SVG (for marp decks) and PDF (for the LaTeX handbook) into a content-hashed
cache, and emit an ordered manifest. Run by the diagram-renderer subagent so
every template embeds identical diagrams.

Manifest schema:
  {"source": "<path>", "d2_theme": N,
   "diagrams": [{"index":0,"hash":"<sha1>","caption":"...",
                 "svg":"<abs>","pdf":"<abs>"}, ...]}
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FENCE = re.compile(r"^(`{3,}|~{3,})\s*(.*)$")
CAPTION = re.compile(r'caption\s*=\s*"([^"]*)"')


def is_d2_info(info: str) -> bool:
    info = info.strip()
    if info == "d2" or info.startswith("d2 "):
        return True
    # pandoc attribute form: {.d2 ...}
    if info.startswith("{") and re.search(r"(^|[\s{.])d2(\s|}|$)", info):
        return True
    return False


def extract_d2(md: str) -> list[tuple[str, str]]:
    """Return ordered list of (d2_source, caption)."""
    out: list[tuple[str, str]] = []
    lines = md.splitlines()
    i, n = 0, len(lines)
    while i < n:
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        fence, info = m.group(1), m.group(2)
        if not is_d2_info(info):
            # skip to matching close so non-d2 fences don't confuse us
            i += 1
            while i < n:
                cm = FENCE.match(lines[i])
                if cm and cm.group(1)[0] == fence[0] and len(cm.group(1)) >= len(fence) and cm.group(2).strip() == "":
                    break
                i += 1
            i += 1
            continue
        cap_m = CAPTION.search(info)
        caption = cap_m.group(1) if cap_m else ""
        body: list[str] = []
        i += 1
        while i < n:
            cm = FENCE.match(lines[i])
            if cm and cm.group(1)[0] == fence[0] and len(cm.group(1)) >= len(fence) and cm.group(2).strip() == "":
                break
            body.append(lines[i])
            i += 1
        i += 1  # consume closing fence
        out.append(("\n".join(body) + "\n", caption))
    return out


def render_one(src: str, cache: Path, theme: int) -> tuple[str, Path, Path]:
    h = hashlib.sha1(f"theme={theme}\n{src}".encode()).hexdigest()[:16]
    d2_file = cache / f"{h}.d2"
    svg = cache / f"{h}.svg"
    pdf = cache / f"{h}.pdf"
    if not svg.exists():
        d2_file.write_text(src)
        subprocess.run(["d2", "--theme", str(theme), str(d2_file), str(svg)],
                       check=True, capture_output=True)
    if not pdf.exists():
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(svg)],
                       check=True, capture_output=True)
    return h, svg, pdf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--d2-theme", type=int, default=0)
    args = ap.parse_args()

    cache = Path(args.cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    md = Path(args.inp).read_text()
    blocks = extract_d2(md)

    diagrams = []
    for idx, (src, caption) in enumerate(blocks):
        try:
            h, svg, pdf = render_one(src, cache, args.d2_theme)
        except subprocess.CalledProcessError as e:
            print(f"d2 render failed for block {idx}: {e.stderr.decode()[:400]}", file=sys.stderr)
            return 2
        diagrams.append({"index": idx, "hash": h, "caption": caption,
                         "svg": str(svg.resolve()), "pdf": str(pdf.resolve())})

    manifest = {"source": str(Path(args.inp).resolve()),
                "d2_theme": args.d2_theme, "diagrams": diagrams}
    Path(args.manifest).write_text(json.dumps(manifest, indent=2))
    print(f"rendered {len(diagrams)} diagram(s) → {args.manifest} (cache: {cache})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
