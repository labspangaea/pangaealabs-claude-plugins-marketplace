#!/usr/bin/env python3
"""docsmith marp preprocessor (marp-cli backend).

Turns a docsmith deck source into a marp-ready markdown: strips the docsmith
front-matter and writes the marp directives (theme/paginate/header/footer). Slide
layout is chosen by the author with marp per-slide directives, e.g.
`<!-- _class: kpi -->`.

Diagrams and art are hand-written raw SVG embedded as markdown images
(`![caption](/abs/x.svg)`); marp embeds them via Chrome, so there is no
pre-render step.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import yaml


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


def build_marp_md(body: str, theme_name: str, *, paginate=True,
                  header: str | None = None, footer: str | None = None) -> str:
    front: dict = {"marp": True, "theme": theme_name, "paginate": paginate}
    if header:
        front["header"] = header
    if footer:
        front["footer"] = footer
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


def prepare(source_md: str, theme_name: str,
            *, header=None, footer=None) -> tuple[str, dict]:
    fm, body = split_frontmatter(source_md)
    return build_marp_md(body, theme_name, header=header, footer=footer), fm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--theme-name", required=True)
    ap.add_argument("--header")
    ap.add_argument("--footer")
    args = ap.parse_args()
    md, _ = prepare(Path(args.inp).read_text(), args.theme_name,
                    header=args.header, footer=args.footer)
    Path(args.out).write_text(md)
    print(f"marp source → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
