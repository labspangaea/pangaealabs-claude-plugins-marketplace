#!/usr/bin/env python3
"""docsmith marp preprocessor (marp-cli backend).

Turns a docsmith deck source into a marp-ready markdown: strips the docsmith
front-matter, writes marp directives (theme/paginate/header/footer), and
replaces each inline ```d2 block (in document order) with the pre-rendered SVG
from the shared diagram manifest. Slide layout is chosen by the author with
marp per-slide directives, e.g. `<!-- _class: kpi -->`.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_diagrams import FENCE, is_d2_info  # shared fence logic


def split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + 4:].lstrip("\n")
            try:
                data = yaml.safe_load(fm) or {}
            except yaml.YAMLError:
                data = {}
            return data, body
    return {}, text


def inject_diagrams(body: str, diagrams: list[dict]) -> str:
    lines = body.splitlines()
    out: list[str] = []
    i, n, k = 0, len(lines), 0
    while i < n:
        m = FENCE.match(lines[i])
        if m and is_d2_info(m.group(2)):
            fence = m.group(1)
            i += 1
            while i < n:
                cm = FENCE.match(lines[i])
                if cm and cm.group(1)[0] == fence[0] and len(cm.group(1)) >= len(fence) and cm.group(2).strip() == "":
                    break
                i += 1
            i += 1  # consume close
            if k < len(diagrams):
                d = diagrams[k]
                out.append(f'![{d.get("caption", "")}]({d["svg"]})')
            k += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def build_marp_md(body: str, theme_name: str, *, paginate=True,
                  header: str | None = None, footer: str | None = None) -> str:
    front: dict = {"marp": True, "theme": theme_name, "paginate": paginate}
    if header:
        front["header"] = header
    if footer:
        front["footer"] = footer
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


def prepare(source_md: str, manifest_path: str | None, theme_name: str,
            *, header=None, footer=None) -> tuple[str, dict]:
    fm, body = split_frontmatter(source_md)
    diagrams: list[dict] = []
    if manifest_path and Path(manifest_path).exists():
        diagrams = json.loads(Path(manifest_path).read_text()).get("diagrams", [])
    body = inject_diagrams(body, diagrams)
    return build_marp_md(body, theme_name, header=header, footer=footer), fm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--theme-name", required=True)
    ap.add_argument("--diagrams-manifest")
    ap.add_argument("--header")
    ap.add_argument("--footer")
    args = ap.parse_args()
    md, _ = prepare(Path(args.inp).read_text(), args.diagrams_manifest,
                    args.theme_name, header=args.header, footer=args.footer)
    Path(args.out).write_text(md)
    print(f"marp source → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
