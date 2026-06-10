#!/usr/bin/env python3
"""docsmith doctor — verify the external toolchain is present.

Exit non-zero if any REQUIRED tool for the requested backend(s) is missing.
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys

# tool -> (probe args, install hint)
TOOLS = {
    "d2": (["--version"], "brew install d2"),
    "pandoc": (["--version"], "brew install pandoc"),
    "tectonic": (["--version"], "brew install tectonic"),
    "rsvg-convert": (["--version"], "brew install librsvg"),
    "npx": (["--version"], "install Node.js (brew install node / asdf)"),
    "pdfinfo": (["-v"], "brew install poppler"),
}

# which tools each backend needs
BACKEND_TOOLS = {
    "pandoc-tectonic": ["pandoc", "tectonic", "d2", "rsvg-convert", "pdfinfo"],
    "marp-cli": ["npx", "d2", "rsvg-convert", "pdfinfo"],
}


def have(tool: str) -> bool:
    if shutil.which(tool) is None:
        return False
    args, _ = TOOLS[tool]
    try:
        subprocess.run([tool, *args], capture_output=True, timeout=20)
        return True
    except Exception:
        return False


def chrome_path() -> str | None:
    import os
    for env in ("CHROME_PATH", "PUPPETEER_EXECUTABLE_PATH"):
        p = os.environ.get(env)
        if p and shutil.which(p) or (p and __import__("pathlib").Path(p).exists()):
            return p
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for c in candidates:
        if c and __import__("pathlib").Path(c).exists():
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=list(BACKEND_TOOLS), action="append",
                    help="check only this backend's tools (repeatable); default = all")
    args = ap.parse_args()
    backends = args.backend or list(BACKEND_TOOLS)
    needed = sorted({t for b in backends for t in BACKEND_TOOLS[b]})

    ok = True
    print(f"docsmith doctor — checking backends: {', '.join(backends)}")
    for t in needed:
        present = have(t)
        print(f"  [{'OK ' if present else 'MISS'}] {t}" + ("" if present else f"  → {TOOLS[t][1]}"))
        ok = ok and present

    if "marp-cli" in backends:
        cp = chrome_path()
        print(f"  [{'OK ' if cp else 'WARN'}] headless Chrome" +
              (f"  ({cp})" if cp else "  → install Google Chrome, or set CHROME_PATH"))
        # marp can also download its own chromium; treat as warning only.

    if not ok:
        print("\nMissing required tools — install the above and re-run.", file=sys.stderr)
        return 1
    print("\nAll required tools present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
