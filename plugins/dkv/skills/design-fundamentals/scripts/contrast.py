#!/usr/bin/env python3
"""WCAG contrast ratios for a set of colour pairs.

Every review needs this and the arithmetic never changes, so it lives here rather
than being rewritten per invocation. Reports the ratio and the verdict against the
threshold that actually applies — which depends on what the colour is *for*, not
just on the two colours:

    body        4.5:1   text below 18pt (24px), or below 14pt (18.66px) bold
    large       3.0:1   text at/above those sizes
    ui          3.0:1   NON-TEXT: component borders, focus rings, icons, chart
                        strokes, and any boundary a user must perceive (WCAG 1.4.11)
    aaa         7.0:1   Level AAA body

The `ui` case is the one reviews miss. A button whose label passes at 13:1 can
still have a border at 2:1, and the border is what tells you the button is there.

Usage:
    python3 contrast.py "#F8CDD7" "#270710"              # ratio only
    python3 contrast.py "#713946" "#270710" ui           # ratio + verdict
    python3 contrast.py --pairs pairs.tsv                # fg<TAB>bg<TAB>kind<TAB>label
    python3 contrast.py --selfcheck
"""
import sys

THRESHOLDS = {"body": 4.5, "large": 3.0, "ui": 3.0, "aaa": 7.0}


def _luminance(hex_colour: str) -> float:
    h = hex_colour.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) not in (6, 8):
        raise ValueError(f"not a hex colour: {hex_colour!r}")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(fg: str, bg: str) -> float:
    """Contrast ratio between two opaque colours, 1.0–21.0."""
    a, b = _luminance(fg), _luminance(bg)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


def check(fg: str, bg: str, kind: str = "body") -> tuple:
    """Returns (ratio, threshold, passed)."""
    if kind not in THRESHOLDS:
        raise ValueError(f"kind must be one of {sorted(THRESHOLDS)}, got {kind!r}")
    r = ratio(fg, bg)
    need = THRESHOLDS[kind]
    return r, need, r >= need


def _selfcheck() -> None:
    # anchors from the WCAG spec: identical colours floor at 1, black/white caps at 21
    assert ratio("#000000", "#FFFFFF") == 21.0, "black on white must be 21:1"
    assert ratio("#FFFFFF", "#FFFFFF") == 1.0, "identical colours must be 1:1"
    assert ratio("#000", "#FFF") == 21.0, "3-digit hex must expand"
    assert ratio("#270710", "#F8CDD7") == ratio("#F8CDD7", "#270710"), "must be symmetric"
    # a real case: a border that passes as large text but fails as a UI boundary
    r, need, ok = check("#713946", "#270710", "ui")
    assert not ok and need == 3.0, f"expected UI fail, got {r} vs {need}"
    # and one that passes
    _, _, ok = check("#F8CDD7", "#270710", "body")
    assert ok, "light-on-dark body pair should pass"
    print("selfcheck ok")


def main(argv: list) -> int:
    if "--selfcheck" in argv:
        _selfcheck()
        return 0

    if "--pairs" in argv:
        path = argv[argv.index("--pairs") + 1]
        rows = []
        with open(path) as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                parts = line.split("\t")
                fg, bg = parts[0], parts[1]
                kind = parts[2] if len(parts) > 2 else "body"
                label = parts[3] if len(parts) > 3 else ""
                rows.append((label or f"{fg} on {bg}", fg, bg, kind))
        width = max((len(r[0]) for r in rows), default=10)
        fails = 0
        for label, fg, bg, kind in rows:
            r, need, ok = check(fg, bg, kind)
            if not ok:
                fails += 1
            print(f"{label:<{width}}  {r:>6}:1  {kind:<5} need {need}  {'pass' if ok else 'FAIL'}")
        print(f"\n{len(rows)} pairs, {fails} failing")
        return 1 if fails else 0

    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    fg, bg = args[0], args[1]
    kind = args[2] if len(args) > 2 else None
    if kind:
        r, need, ok = check(fg, bg, kind)
        print(f"{r}:1  {kind} needs {need}  {'pass' if ok else 'FAIL'}")
        return 0 if ok else 1
    print(f"{ratio(fg, bg)}:1")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
