#!/usr/bin/env python3
"""docsmith build — render ONE template of a source document to PDF.

Merges config (template defaults → ~/.docsmith/template/<name>.yaml → profile →
doc front-matter/overrides → CLI), then dispatches on the template's backend:
  - pandoc-tectonic : LaTeX book → PDF (handbook)
  - marp-cli        : 16:9 slides → PDF (decks)

Diagrams and art are hand-written raw SVG embedded as markdown images. There is
no pre-render step: the handbook converts SVG→PDF via rsvg-convert (pandoc's
native SVG handling) and the decks embed SVG via Chrome (marp), so the same .svg
renders consistently across every template.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent
PLUGIN = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import marp_prep  # noqa: E402


def load_yaml(p: Path) -> dict:
    if p and p.exists():
        return yaml.safe_load(p.read_text()) or {}
    return {}


def _render_log(line: str) -> None:
    """Append one render result to ~/.docsmith/render.log (best-effort).

    The docsmith plugin ships a background monitor (monitors/monitors.json) that
    tails this file, so every build — including the parallel multi-template
    fan-out and renders triggered by subagents — surfaces in the session as a
    notification. Logging must never break a build, so all errors are swallowed.
    """
    try:
        log_dir = Path(os.path.expanduser("~/.docsmith"))
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = _dt.datetime.now().strftime("%H:%M:%S")
        with open(log_dir / "render.log", "a") as fh:
            fh.write(f"{ts} {line}\n")
    except Exception:
        pass


def _run_capturing(cmd, **kwargs):
    """Run a backend command, capturing its stderr so a failure can be logged with a
    real root cause, while still surfacing that stderr to the terminal. Returns
    (returncode, stderr_text)."""
    r = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, **kwargs)
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode, (r.stderr or "")


def _write_error_log(template: str, rc: int, out, stderr_text: str) -> str:
    """On a failed render, write the backend's stderr tail to
    ~/.docsmith/render-errors/<ts>-<template>.log and return its path (best-effort).

    This gives the render.log FAIL line — and any triage tooling watching it — an
    actual root cause (the pandoc/marp/tectonic error) instead of just an exit code.
    """
    try:
        d = Path(os.path.expanduser("~/.docsmith/render-errors"))
        d.mkdir(parents=True, exist_ok=True)
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        p = d / f"{ts}-{template}.log"
        tail = "\n".join((stderr_text or "").splitlines()[-40:])
        p.write_text(f"# docsmith render FAIL — {template} (rc={rc})\n# out: {out}\n\n{tail}\n")
        return str(p)
    except Exception:
        return ""


def resolve_org(profile_raw, chosen_name: str | None):
    """Collapse a profile into the single effective org dict.

    The profile may be either:
      - a LIST of self-contained org dicts (new format) — pick the one whose
        `company` matches `chosen_name` (case-insensitive), else the first; or
      - a DICT (legacy format) — returned unchanged so the existing flat /
        company-array+logos / plain-string handling downstream still applies.

    `chosen_name` is the requested company (CLI > front-matter); it only steers
    selection within a LIST profile. A list is never returned to callers.

    The fall-back-to-first here is for the implicit default only (no company
    requested at all): `main()` rejects an *explicit* company that matches no org
    before calling this, so a typo'd name errors instead of silently mis-stamping.
    """
    if isinstance(profile_raw, list):
        orgs = [o for o in profile_raw if isinstance(o, dict)]
        if not orgs:
            return {}
        if chosen_name:
            target = str(chosen_name).strip().lower()
            for o in orgs:
                if str(o.get("company", "")).strip().lower() == target:
                    return o
        return orgs[0]
    if isinstance(profile_raw, dict):
        return profile_raw
    return {}


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def docsmith_home() -> Path:
    return Path(os.environ.get("DOCSMITH_HOME", Path.home() / ".docsmith"))


def chosen_company(value, override: str | None = None) -> str:
    """Collapse `company` to a single string for the cover.

    `company` may be a plain string (legacy) or a list (pick the first).
    A CLI `--company` override wins over both. Never returns a list.
    """
    if override:
        return str(override)
    if isinstance(value, (list, tuple)):
        return str(value[0]) if value else ""
    return str(value) if value else ""


def split_frontmatter(text: str):
    return marp_prep.split_frontmatter(text)


# ---------- token rendering ----------------------------------------------------

def flatten_colors(colors: dict) -> dict[str, str]:
    """{'navy': {'700': '#003060'}} -> {'navy-700': '#003060'}; flat passthrough too."""
    out: dict[str, str] = {}
    for k, v in (colors or {}).items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                out[f"{k}-{sk}"] = str(sv)
        else:
            out[k] = str(v)
    return out


def hex_only(value: str) -> str:
    return value.lstrip("#")


def render_tokens_tex(ds: dict) -> str:
    """Emit \\definecolor for every color + a few length/macro tokens."""
    lines = ["% docsmith generated tokens — do not edit", "\\usepackage{xcolor}"]
    for name, val in flatten_colors(ds.get("colors", {})).items():
        if val.startswith("#") or len(val) in (3, 6):
            lines.append(f"\\definecolor{{{name}}}{{HTML}}{{{hex_only(val)}}}")
    typ = ds.get("type", {})
    if typ.get("base_size"):
        lines.append(f"\\newcommand{{\\dsbasesize}}{{{typ['base_size']}}}")
    return "\n".join(lines) + "\n"


import re as _re
_URL = _re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")


def _absolutize_urls(css: str, base: Path) -> str:
    def repl(m):
        path = m.group(2).strip()
        if path.startswith(("http://", "https://", "data:", "/")):
            return m.group(0)
        return f'url("{(base / path).resolve()}")'
    return _URL.sub(repl, css)


def render_tokens_css(ds_css_files: list[Path], theme_name: str,
                      overrides: dict, profile: dict) -> str:
    parts = [f"/* @theme {theme_name} */"]
    for f in ds_css_files:
        if f.exists():
            parts.append(f"/* --- {f.name} --- */")
            parts.append(_absolutize_urls(f.read_text(), f.parent))
    root: list[str] = []
    for k, v in (overrides or {}).items():
        root.append(f"  --{k}: {v};")
    # expose a couple of profile-derived vars themes may use
    company = chosen_company(profile.get("company"))
    if company:
        root.append(f'  --ds-company: "{company}";')
    if root:
        parts.append(":root{\n" + "\n".join(root) + "\n}")
    return "\n\n".join(parts) + "\n"


# ---------- backends -----------------------------------------------------------

def meta_value(merged: dict, profile: dict, key: str, default=""):
    val = merged.get(key) or profile.get(key) or default
    # a list must never reach the rendered cover (e.g. a multi-company profile
    # that wasn't collapsed) — fall back to its first element defensively.
    if isinstance(val, (list, tuple)):
        return str(val[0]) if val else default
    return val


def _tex_escape(s: str) -> str:
    s = str(s)
    repl = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(repl.get(c, c) for c in s)


def build_handbook(tmpl_dir: Path, manifest: dict, merged: dict,
                   profile: dict, src: Path, out: Path) -> tuple[int, str]:
    ds = load_yaml(tmpl_dir / "design-system.yaml")
    ds = deep_merge(ds, {"colors": merged.get("overrides", {}).get("colors", {})})
    tmp = Path(tempfile.mkdtemp(prefix="docsmith-hb-"))
    tokens = tmp / "_tokens.tex"
    tokens.write_text(render_tokens_tex(ds))

    assets = tmpl_dir / "assets"
    headers = [tokens] + [assets / h for h in manifest.get("header_includes", [])]
    lua = [assets / f for f in manifest.get("lua_filters", [])]

    date = merged.get("date") or "auto"
    if date == "auto":
        date = _dt.date.today().strftime("%B %Y")   # book-style "June 2026", not ISO

    # config-driven cover + frontmatter/mainmatter injected as raw LaTeX before the body
    cov = {"dstitle": meta_value(merged, profile, "title"),
           "dssubtitle": meta_value(merged, profile, "subtitle"),
           "dsauthor": meta_value(merged, profile, "author"),
           "dscompany": meta_value(merged, profile, "company"),
           "dsversion": meta_value(merged, profile, "version"),
           "dsdate": date,
           # full org profile (for the author/colophon page) — empty fields are
           # guarded in titlepage.tex so they never print blank labels.
           "dsemail": meta_value(merged, profile, "email"),
           "dswebsite": meta_value(merged, profile, "website"),
           "dscopyright": meta_value(merged, profile, "copyright"),
           "dsconfidentiality": meta_value(merged, profile, "default_confidentiality"),
           "dswordmark": meta_value(merged, profile, "wordmark")}
    prefix = "".join(f"\\def\\{k}{{{_tex_escape(v)}}}\n" for k, v in cov.items())
    # logo path (raw, not tex-escaped — it's a filename for \includegraphics)
    logo = meta_value(merged, profile, "logo")
    logo_path = ""
    if logo:
        lp = Path(str(logo)).expanduser()
        if lp.exists():
            logo_path = str(lp.resolve())
    prefix += f"\\def\\dslogo{{{logo_path}}}\n"
    # Digital-first by default: a docsmith handbook is read on screen, where the
    # book class's twoside+openright behaviour inserts a blank verso before every
    # chapter (to land it on a physical right-hand page) plus a trailing blank —
    # those read as broken "empty pages" in a PDF. The template default is now
    # oneside+openany (template.yaml), but geometry's inner/outer margins silently
    # re-enable twoside, so passing the class option isn't enough — flip the flags
    # directly so \cleardoublepage stops emitting blank verso pages. A doc headed
    # for print-and-bind opts back in with `overrides.classoptions: [twoside,
    # openright]`: that keeps the flags AND wins at the class level (appended last).
    classopts = merged.get("overrides", {}).get("classoptions") or []
    if "twoside" not in classopts:
        prefix += "\\makeatletter\\@twosidefalse\\@mparswitchfalse\\makeatother\n"
    if "openright" not in classopts:
        prefix += "\\makeatletter\\@openrightfalse\\makeatother\n"
    # \dscover ends with \clearpage; the TOC's own \chapter* handles clearing,
    # so no extra \cleardoublepage here — it would force a blank verso before the TOC.
    prefix += "\\frontmatter\n\\dscover\n\\dsauthorpage\n\\tableofcontents\n\\mainmatter\n\n"
    body_src = tmp / "body.md"
    # strip the YAML front-matter so pandoc doesn't also emit \maketitle
    # (docsmith already parsed it into `merged`; the cover is drawn by \dscover)
    raw = _re.sub(r"\A---\n.*?\n---\n", "", src.read_text(), count=1, flags=_re.DOTALL)
    body_src.write_text(prefix + raw)

    cmd = ["pandoc", str(body_src), "-o", str(out), "--pdf-engine=tectonic"]
    cmd += manifest.get("pandoc_args", [])
    # per-document LaTeX class options (e.g. [oneside, openany] to drop blank
    # verso pages between short chapters); appended last so they win conflicts
    for opt in (merged.get("overrides", {}).get("classoptions") or []):
        cmd += ["-V", f"classoption={opt}"]
    for h in headers:
        cmd += ["-H", str(h)]
    for f in lua:
        cmd += ["--lua-filter", str(f)]
    return _run_capturing(cmd)


def build_marp(tmpl_dir: Path, manifest: dict, merged: dict,
               profile: dict, src: Path, out: Path) -> tuple[int, str]:
    theme_name = manifest.get("theme_name", f"docsmith-{tmpl_dir.name}")
    assets = tmpl_dir / "assets"
    ds_css = [tmpl_dir / "design-system.css"] + [assets / f for f in manifest.get("theme_files", [])]
    overrides = merged.get("overrides", {}).get("tokens", {})
    tmp = Path(tempfile.mkdtemp(prefix="docsmith-marp-"))
    theme_css = tmp / "theme.css"
    theme_css.write_text(render_tokens_css(ds_css, theme_name, overrides, profile))

    company = meta_value(merged, profile, "company")
    author = meta_value(merged, profile, "author")
    copyright_ = meta_value(merged, profile, "copyright")
    logo = meta_value(merged, profile, "logo")
    footer_parts = []
    if logo:
        lp = Path(str(logo)).expanduser()
        if lp.exists():
            footer_parts.append(f"![h:40]({lp.resolve()})")  # marp sizes via h:NN
    text_parts = [str(x) for x in (company, author, copyright_) if x]
    if text_parts:
        footer_parts.append("  ·  ".join(text_parts))
    footer = merged.get("footer") or manifest.get("footer") or (" ".join(footer_parts) if footer_parts else None)
    slides_md, _ = marp_prep.prepare(src.read_text(), theme_name, footer=footer)
    slides_file = tmp / "slides.md"
    slides_file.write_text(slides_md)

    cmd = ["npx", "-y", "@marp-team/marp-cli@latest", str(slides_file),
           "--theme", str(theme_css), "--pdf", "--allow-local-files",
           "-o", str(out)]
    # Raw-HTML passthrough is opt-in per template (template.yaml `html: true`).
    # kawaii-storybook uses it for `<aside class="callout …">` callouts; other
    # decks stay HTML-off so a stray tag renders as visible text, not markup.
    if manifest.get("html"):
        cmd.append("--html")
    env = dict(os.environ)
    env.setdefault("CHROME_PATH", _find_chrome())
    # Close stdin: marp-cli reads stdin when it's an open pipe (e.g. spawned from
    # a detached shell or subagent) and blocks indefinitely waiting for EOF.
    return _run_capturing(cmd, env={k: v for k, v in env.items() if v},
                          stdin=subprocess.DEVNULL)


def _find_chrome() -> str:
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if Path(c).exists():
            return c
    import shutil
    return shutil.which("google-chrome") or shutil.which("chromium") or ""


# ---------- main ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--profile")
    ap.add_argument("--company", help="pick ONE company for the cover (overrides profile)")
    ap.add_argument("--logo", help="logo path for the cover (overrides profile + logos map)")
    args = ap.parse_args()

    tmpl_dir = PLUGIN / "assets" / "templates" / args.template
    if not tmpl_dir.exists():
        print(f"unknown template: {args.template} ({tmpl_dir} missing)", file=sys.stderr)
        return 2
    manifest = load_yaml(tmpl_dir / "template.yaml")
    backend = manifest.get("backend")

    # config layers
    profile_path = Path(args.profile) if args.profile else (docsmith_home() / "profile.yaml")
    profile_raw = load_yaml(profile_path)
    user_override = load_yaml(docsmith_home() / "template" / f"{args.template}.yaml")
    src = Path(args.inp)
    fm, _ = split_frontmatter(src.read_text())

    # --- collapse the profile to ONE effective org dict ------------------------
    # The profile may be a LIST of self-contained orgs (new) or a DICT (legacy).
    # For a list, the chosen org is resolved BEFORE any dict-merge: a list must
    # never reach deep_merge. Front-matter `company` is a plain string.
    if isinstance(profile_raw, list):
        orgs = [o for o in profile_raw if isinstance(o, dict)]
        # An EXPLICIT company (CLI --company or front-matter) that matches no org
        # is a hard error: silently falling back to the first org would stamp the
        # wrong identity (author/email/logo/website) under the requested name.
        # Only the implicit default (no company requested anywhere) may fall back.
        requested = args.company or fm.get("company")
        if requested and orgs:
            names = {str(o.get("company", "")).strip().lower() for o in orgs}
            if str(requested).strip().lower() not in names:
                available = ", ".join(repr(o.get("company")) for o in orgs)
                print(
                    f"unknown company {requested!r} — not in profile {profile_path}.\n"
                    f"  available companies: {available}\n"
                    f"  fix: pass an existing --company, or add this org to the "
                    f"profile (refusing to fall back to the first org).",
                    file=sys.stderr,
                )
                return 2
        default_company = orgs[0].get("company") if orgs else None
        chosen_name = requested or default_company
        profile = resolve_org(profile_raw, chosen_name)
    else:
        profile = resolve_org(profile_raw, None)  # legacy dict, passthrough

    merged = deep_merge(profile, user_override)
    merged = deep_merge(merged, fm)

    # --- resolve a SINGLE company + logo for the cover -------------------------
    # company: --company > chosen org's `company` (new) / first of legacy list or
    # plain string. Never a list.
    chosen = chosen_company(merged.get("company"), args.company)
    # logo: --logo > legacy per-company logos[chosen] > profile/merged `logo`
    # (the new list profile already carries the chosen org's own `logo`). Expand ~.
    logos_map = (profile.get("logos") or merged.get("logos") or {})
    logo = args.logo or logos_map.get(chosen) or meta_value(merged, profile, "logo")
    if logo:
        logo = str(Path(str(logo)).expanduser())
    # pin the resolved singletons into both dicts so every backend + token
    # renderer sees one company string and the chosen logo (no list ever leaks).
    for d in (merged, profile):
        d["company"] = chosen
        if logo:
            d["logo"] = logo

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if backend == "pandoc-tectonic":
        rc, err = build_handbook(tmpl_dir, manifest, merged, profile, src, out)
    elif backend == "marp-cli":
        rc, err = build_marp(tmpl_dir, manifest, merged, profile, src, out)
    else:
        print(f"unknown backend '{backend}' in {tmpl_dir/'template.yaml'}", file=sys.stderr)
        return 2

    if rc != 0:
        errlog = _write_error_log(args.template, rc, out, err)
        _render_log(f"FAIL {args.template} (rc={rc}) {out}"
                    + (f" [err: {errlog}]" if errlog else ""))
        print(f"render failed (backend={backend}, rc={rc})", file=sys.stderr)
        return rc

    try:
        info = subprocess.run(["pdfinfo", str(out)], capture_output=True, text=True).stdout
        pages = next((l.split(":")[1].strip() for l in info.splitlines() if l.startswith("Pages")), "?")
        size = next((l.split(":", 1)[1].strip() for l in info.splitlines() if l.startswith("Page size")), "?")
        print(f"OK  {out}  ({pages} pages, {size})")
        _render_log(f"OK {args.template} {pages}pp {out}")
    except Exception:
        print(f"OK  {out}")
        _render_log(f"OK {args.template} {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
