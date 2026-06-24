#!/usr/bin/env python3
"""Render a canonical test-case CSV into a single-file, offline HTML console.
Generic / parameterized — works with any CSV that uses the canonical columns.

  python render_console.py --csv cases.csv --out cases.html \
      --title "Checkout Test Matrix" --subtitle "Imported cases"
"""
import csv, json, html, argparse, pathlib

ap = argparse.ArgumentParser(description="Render a canonical testcase CSV to an HTML console.")
ap.add_argument("--csv", required=True, help="input CSV using the canonical columns")
ap.add_argument("--out", help="output HTML path (default: alongside the CSV)")
ap.add_argument("--title", default="Test Matrix", help="page + header title")
ap.add_argument("--subtitle", default="Imported test cases", help="header subtitle prefix")
A = ap.parse_args()

csv_path = pathlib.Path(A.csv)
out_path = pathlib.Path(A.out) if A.out else csv_path.with_suffix(".html")

from _schema import CANON  # canonical 10-column contract (shared with normalize_testcases.py)
rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
if not rows:
    raise SystemExit("No rows in %s" % csv_path)
missing = [c for c in CANON if c not in rows[0]]
if missing:
    raise SystemExit("CSV is missing canonical columns: %s\nFound: %s"
                     % (missing, list(rows[0].keys())))

# normalize keys to short names the JS expects
data = [{
    "id": r["ID"], "group": r["Group"], "type": r["Type"], "outcome": r["Outcome"],
    "priority": r["Priority"], "why": r["Severity_Reasoning"], "transition": r["Transition"],
    "title": r["Title"], "steps": r["Steps / Test Data"],
    "expected": r["Expected Result + Downstream Impact / Fix"],
} for r in rows]

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  /* surface — deep cool slate */
  --bg:        oklch(0.165 0.014 256);
  --surface:   oklch(0.205 0.017 256);
  --surface-2: oklch(0.245 0.020 256);
  --raise:     oklch(0.285 0.022 256);
  --line:      oklch(0.32 0.020 256);
  --line-2:    oklch(0.40 0.022 256);
  /* ink */
  --ink:   oklch(0.955 0.008 250);
  --ink-2: oklch(0.80 0.012 250);
  --muted: oklch(0.645 0.014 250);
  /* ui accent — cool cyan, distinct from severity greens/reds */
  --accent:    oklch(0.78 0.12 208);
  --accent-dim:oklch(0.78 0.12 208 / 0.14);
  /* severity / outcome inks */
  --crit:  oklch(0.70 0.185 25);
  --major: oklch(0.82 0.135 75);
  --minor: oklch(0.70 0.030 250);
  --low:   oklch(0.58 0.020 250);
  --tn:    oklch(0.80 0.145 158);
  --tp:    oklch(0.78 0.115 222);
  --fp:    oklch(0.83 0.130 80);
  --fn:    oklch(0.70 0.185 25);

  --mono: "SF Mono", ui-monospace, "JetBrains Mono", Menlo, Consolas, "Liberation Mono", monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;

  --z-sticky: 100;
  --r: 7px;
  --e-out: cubic-bezier(0.22, 1, 0.36, 1);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--sans); font-size:14px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
  background-image:
    radial-gradient(120% 80% at 100% 0%, oklch(0.78 0.12 208 / 0.05), transparent 60%),
    radial-gradient(100% 70% at 0% 0%, oklch(0.70 0.185 25 / 0.035), transparent 55%);
}
.wrap{max-width:1280px; margin:0 auto; padding:0 clamp(14px,3vw,28px)}

/* ── header ── */
header.top{
  position:sticky; top:0; z-index:var(--z-sticky);
  background:oklch(0.165 0.014 256 / 0.86); backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);
}
.top-in{display:flex; flex-wrap:wrap; gap:14px 24px; align-items:center; padding:14px 0}
.brand{display:flex; align-items:baseline; gap:10px; min-width:0}
.brand .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 3px var(--accent-dim); flex:none; align-self:center}
.brand h1{font-family:var(--mono); font-size:15px; font-weight:600; letter-spacing:.02em;
  margin:0; text-transform:uppercase; white-space:nowrap}
.brand .sub{font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.04em}
.stats{display:flex; gap:18px; align-items:center; margin-left:auto; flex-wrap:wrap}
.stat{font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.03em;
  display:flex; align-items:baseline; gap:6px; white-space:nowrap}
.stat b{font-size:16px; color:var(--ink); font-weight:600; letter-spacing:0}
.stat.crit b{color:var(--crit)} .stat.fn b{color:var(--fn)}
/* distribution bar */
.dist{display:flex; height:8px; width:clamp(180px,22vw,260px); border-radius:99px;
  overflow:hidden; background:var(--surface); outline:1px solid var(--line)}
.dist span{display:block; height:100%}
.dist .s-fn{background:var(--fn)} .dist .s-tp{background:var(--tp)}
.dist .s-tn{background:var(--tn)} .dist .s-fp{background:var(--fp)}

/* ── toolbar ── */
.toolbar{position:sticky; top:53px; z-index:calc(var(--z-sticky) - 1);
  background:oklch(0.165 0.014 256 / 0.92); backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line); padding:12px 0}
.search-row{display:flex; gap:10px; align-items:center; margin-bottom:11px}
.search{flex:1; position:relative; min-width:0}
.search input{width:100%; font-family:var(--mono); font-size:13px; color:var(--ink);
  background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
  padding:9px 12px 9px 34px; outline:none; transition:border-color .15s, box-shadow .15s}
.search input::placeholder{color:var(--muted)}
.search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-dim)}
.search svg{position:absolute; left:11px; top:50%; transform:translateY(-50%);
  width:15px;height:15px; color:var(--muted); pointer-events:none}
.search kbd{position:absolute; right:9px; top:50%; transform:translateY(-50%);
  font-family:var(--mono); font-size:10px; color:var(--muted);
  border:1px solid var(--line-2); border-radius:4px; padding:1px 5px; background:var(--bg)}
.search input:not(:placeholder-shown) ~ kbd{opacity:0}
.sortwrap{display:flex; align-items:center; gap:7px; font-family:var(--mono);
  font-size:11px; color:var(--muted); white-space:nowrap}
.sortwrap select{font-family:var(--mono); font-size:12px; color:var(--ink);
  background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
  padding:8px 10px; outline:none; cursor:pointer}
.sortwrap select:focus{border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-dim)}

.facets{display:flex; flex-direction:column; gap:7px}
.facet{display:flex; flex-wrap:wrap; gap:6px; align-items:center}
.facet > .lbl{font-family:var(--mono); font-size:10px; letter-spacing:.09em;
  color:var(--muted); text-transform:uppercase; width:64px; flex:none}
.chip{font-family:var(--mono); font-size:11.5px; color:var(--ink-2); cursor:pointer;
  background:var(--surface); border:1px solid var(--line); border-radius:99px;
  padding:4px 11px; display:inline-flex; align-items:center; gap:6px; user-select:none;
  transition:border-color .14s, background .14s, color .14s; white-space:nowrap}
.chip:hover{border-color:var(--line-2); color:var(--ink)}
.chip:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.chip .n{font-size:10px; color:var(--muted); font-variant-numeric:tabular-nums}
.chip[aria-pressed="true"]{background:var(--accent-dim); border-color:var(--accent); color:var(--ink)}
.chip[aria-pressed="true"] .n{color:var(--accent)}
/* outcome/sev chips carry their own hue when active */
.chip.c-fn[aria-pressed="true"]{background:oklch(0.70 0.185 25 /.16); border-color:var(--fn); color:var(--fn)}
.chip.c-fn[aria-pressed="true"] .n{color:var(--fn)}
.chip.c-crit[aria-pressed="true"]{background:oklch(0.70 0.185 25 /.16); border-color:var(--crit); color:var(--crit)}
.chip.c-crit[aria-pressed="true"] .n{color:var(--crit)}
.chip .swatch{width:7px;height:7px;border-radius:2px;flex:none}
.clearbtn{font-family:var(--mono); font-size:11px; color:var(--crit); cursor:pointer;
  background:none; border:none; padding:4px 6px; margin-left:2px; opacity:0; pointer-events:none;
  transition:opacity .14s}
.clearbtn.show{opacity:1; pointer-events:auto}
.clearbtn:hover{text-decoration:underline}

/* ── list ── */
main{padding:18px 0 80px}
.count{font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.03em;
  padding:0 2px 11px; display:flex; justify-content:space-between; align-items:center}
.count b{color:var(--ink-2); font-weight:600}
.thead{display:grid; gap:14px; align-items:center; padding:0 14px 8px;
  grid-template-columns:5.5rem 4rem 3.5rem 8.5rem minmax(0,1fr) 1.1rem;
  font-family:var(--mono); font-size:10px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); border-bottom:1px solid var(--line)}
.list{display:flex; flex-direction:column}

.row{border-bottom:1px solid var(--line); background:transparent;
  transition:background .14s}
.row[data-tier="crit"]{background:oklch(0.70 0.185 25 / 0.045)}
.row:hover{background:var(--surface)}
.row[data-tier="crit"]:hover{background:oklch(0.70 0.185 25 / 0.075)}
.row > summary{display:grid; gap:14px; align-items:center; padding:11px 14px; cursor:pointer;
  grid-template-columns:5.5rem 4rem 3.5rem 8.5rem minmax(0,1fr) 1.1rem; list-style:none}
.row > summary::-webkit-details-marker{display:none}
.row > summary:focus-visible{outline:2px solid var(--accent); outline-offset:-2px; border-radius:4px}
.c-id{font-family:var(--mono); font-size:12.5px; font-weight:600; color:var(--ink); letter-spacing:.01em}
.c-meta{display:contents}
.c-sec{font-family:var(--mono); font-size:11px; color:var(--ink-2); white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis}
.c-title{font-size:13.5px; color:var(--ink); min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.caret{justify-self:end; color:var(--muted); transition:transform .25s var(--e-out); font-size:13px}
.row[open] .caret{transform:rotate(90deg)}

.pill{font-family:var(--mono); font-size:10.5px; font-weight:600; letter-spacing:.02em;
  padding:2px 7px; border-radius:5px; display:inline-flex; justify-self:start; white-space:nowrap;
  border:1px solid transparent}
.pill.sev-crit{color:var(--crit); background:oklch(0.70 0.185 25 /.13); border-color:oklch(0.70 0.185 25 /.4)}
.pill.sev-major{color:var(--major);background:oklch(0.82 0.135 75 /.12); border-color:oklch(0.82 0.135 75 /.34)}
.pill.sev-minor{color:var(--minor);background:oklch(0.70 0.03 250 /.14); border-color:var(--line-2)}
.pill.sev-low{color:var(--low); background:oklch(0.58 0.02 250 /.12); border-color:var(--line)}
.pill.out-TN{color:var(--tn); background:oklch(0.80 0.145 158 /.12); border-color:oklch(0.80 0.145 158 /.32)}
.pill.out-TP{color:var(--tp); background:oklch(0.78 0.115 222 /.12); border-color:oklch(0.78 0.115 222 /.32)}
.pill.out-FP{color:var(--fp); background:oklch(0.83 0.13 80 /.12); border-color:oklch(0.83 0.13 80 /.32)}
.pill.out-FN{color:var(--fn); background:oklch(0.70 0.185 25 /.14); border-color:oklch(0.70 0.185 25 /.42)}

/* detail — animated open */
.detail{display:grid; grid-template-rows:0fr; transition:grid-template-rows .28s var(--e-out)}
.row[open] .detail{grid-template-rows:1fr}
.detail-in{overflow:hidden; min-height:0}
.detail-pad{padding:4px 14px 18px; padding-left:calc(5.5rem + 28px)}
@media (max-width:760px){ .detail-pad{padding-left:14px} }
.detail dl{display:grid; grid-template-columns:max-content minmax(0,1fr); gap:8px 18px; margin:0; max-width:78ch}
.detail dt{font-family:var(--mono); font-size:10px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); padding-top:2px}
.detail dd{margin:0; color:var(--ink-2); font-size:13px; line-height:1.6; text-wrap:pretty}
.detail dd.mono{font-family:var(--mono); font-size:12px; color:var(--ink)}
.detail dd.why{color:var(--ink-2)}
.detail dd.why::before{content:""; display:inline-block; width:6px;height:6px;border-radius:50%;
  background:currentColor; margin-right:8px; vertical-align:middle; opacity:.5}
.tagline{display:flex; gap:8px; flex-wrap:wrap; margin-top:2px}
.tagline .pill{justify-self:auto}

/* empty */
.empty{text-align:center; padding:64px 20px; color:var(--muted); font-family:var(--mono); font-size:13px}
.empty b{color:var(--ink-2); display:block; font-size:15px; margin-bottom:6px}
.empty button{margin-top:16px; font-family:var(--mono); font-size:12px; color:var(--accent);
  background:var(--accent-dim); border:1px solid var(--accent); border-radius:var(--r);
  padding:8px 16px; cursor:pointer}

footer{border-top:1px solid var(--line); padding:22px 0 40px; color:var(--muted);
  font-family:var(--mono); font-size:11px; letter-spacing:.02em; text-align:center}

/* ── legend button + glossary dialog ── */
.legend-btn{font-family:var(--mono); font-size:11px; letter-spacing:.04em; color:var(--ink-2);
  background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
  padding:6px 12px; cursor:pointer; display:inline-flex; align-items:center; gap:7px;
  transition:border-color .14s, color .14s}
.legend-btn:hover{border-color:var(--accent); color:var(--ink)}
.legend-btn:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.legend-btn::before{content:"?"; font-weight:700; color:var(--accent); width:15px;height:15px;
  border:1px solid var(--line-2); border-radius:4px; display:inline-grid; place-items:center; font-size:10px}

dialog.legend{border:1px solid var(--line-2); border-radius:12px; padding:0; color:var(--ink);
  width:min(640px,92vw); max-height:86vh; background:var(--surface);
  box-shadow:0 24px 64px oklch(0 0 0 /.5); overflow:hidden}
dialog.legend::backdrop{background:oklch(0.12 0.01 256 /.62); backdrop-filter:blur(3px)}
dialog.legend[open]{display:flex; flex-direction:column; animation:dlg .26s var(--e-out)}
@keyframes dlg{from{opacity:0; transform:translateY(10px) scale(.985)} to{opacity:1; transform:none}}
.lg-head{display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:15px 20px; border-bottom:1px solid var(--line); background:var(--surface)}
.lg-head h2{font-family:var(--mono); font-size:13px; font-weight:600; letter-spacing:.05em;
  text-transform:uppercase; margin:0}
.lg-x{font-family:var(--mono); font-size:11px; color:var(--muted); background:none;
  border:1px solid var(--line); border-radius:6px; padding:5px 10px; cursor:pointer}
.lg-x:hover{color:var(--ink); border-color:var(--line-2)}
.lg-x:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.lg-body{padding:18px 20px 22px; overflow:auto}
.lg-body section{margin:0 0 20px}
.lg-body h3{font-family:var(--mono); font-size:10.5px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); margin:0 0 11px; font-weight:600}
.lg-defs{display:grid; grid-template-columns:max-content 1fr; gap:10px 16px; margin:0; align-items:start}
.lg-defs dt{padding-top:1px}
.lg-defs dd{margin:0; color:var(--ink-2); font-size:13px; line-height:1.55; text-wrap:pretty}
.lg-defs dd b{color:var(--ink); font-weight:600}
.lg-line{color:var(--ink-2); font-size:13px; line-height:1.7; margin:0}
.lg-line code,.lg-states code{font-family:var(--mono); color:var(--ink); background:var(--bg);
  border:1px solid var(--line); border-radius:4px; padding:1px 6px; font-size:12px; white-space:nowrap}
.lg-states{display:grid; gap:10px}
.lg-states .row2{display:flex; gap:10px; align-items:baseline}
.lg-states .tag{font-family:var(--mono); font-size:10px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); width:58px; flex:none; padding-top:3px}
.lg-tbl{width:100%; border-collapse:collapse; font-size:12.5px}
.lg-tbl th,.lg-tbl td{border:1px solid var(--line); padding:8px 11px; text-align:left}
.lg-tbl th{font-family:var(--mono); font-size:10px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); font-weight:600; background:var(--bg)}
.lg-tbl td{color:var(--ink-2)} .lg-tbl td b{color:var(--ink); font-family:var(--mono); font-weight:600}
.caution{color:var(--fn); font-weight:600}
.lg-caution{display:flex; gap:11px; align-items:flex-start;
  background:oklch(0.70 0.185 25 /.08); border:1px solid oklch(0.70 0.185 25 /.32);
  border-radius:8px; padding:12px 14px; color:var(--ink-2); font-size:12.5px; line-height:1.55}
.lg-caution .mk{color:var(--fn); font-size:15px; line-height:1.2; flex:none}
.lg-caution b{color:var(--fn)}
.lg-caution b.ink{color:var(--ink)}

/* entrance */
@keyframes rowin{from{opacity:0; transform:translateY(6px)} to{opacity:1; transform:none}}
.row.enter{animation:rowin .42s var(--e-out) backwards; animation-delay:var(--d,0ms)}

@media (max-width:760px){
  .thead{display:none}
  .row > summary{grid-template-columns:1fr auto; gap:7px 10px; row-gap:8px}
  .c-id{order:0}
  .caret{order:1}
  .c-title{order:2; grid-column:1 / -1; white-space:normal}
  .c-meta{display:flex; order:3; grid-column:1 / -1; gap:7px; flex-wrap:wrap; align-items:center}
}
@media (prefers-reduced-motion:reduce){
  *{scroll-behavior:auto}
  .detail{transition:none}
  .caret{transition:none}
  .row.enter{animation:none}
  header.top,.toolbar{backdrop-filter:none}
  dialog.legend[open]{animation:none}
  dialog.legend::backdrop{backdrop-filter:none}
}
</style>
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <div class="brand">
      <span class="dot" aria-hidden="true"></span>
      <h1>__TITLE__</h1>
      <span class="sub" id="srcline"></span>
    </div>
    <div class="stats">
      <span class="stat"><b id="st-total">0</b> cases</span>
      <span class="stat crit"><b id="st-crit">0</b> critical</span>
      <span class="stat fn"><b id="st-fn">0</b> FN!</span>
      <div class="dist" id="dist" role="img" aria-label="outcome distribution"></div>
    </div>
    <button class="legend-btn" id="openLegend" type="button" aria-haspopup="dialog">legend</button>
  </div>
</header>

<div class="toolbar">
  <div class="wrap">
    <div class="search-row">
      <label class="search">
        <span class="visually-hidden" hidden>Search test cases</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="q" type="search" placeholder="search id, title, steps, fix…" autocomplete="off" spellcheck="false" aria-label="Search test cases">
        <kbd>/</kbd>
      </label>
      <div class="sortwrap">
        <label for="sort">sort</label>
        <select id="sort">
          <option value="sev">severity</option>
          <option value="id">id</option>
          <option value="section">section</option>
        </select>
      </div>
    </div>
    <div class="facets" id="facets"></div>
  </div>
</div>

<main class="wrap">
  <div class="count"><span id="count">—</span><button class="clearbtn" id="clear">clear filters ✕</button></div>
  <div class="thead" aria-hidden="true">
    <span>ID</span><span>SEV</span><span>OUT</span><span>SECTION</span><span>CASE</span><span></span>
  </div>
  <div class="list" id="list"></div>
</main>

<footer class="wrap">Generated from travel-card-testcases.csv · 1 file · offline · keyboard: / search · ? legend · esc clear</footer>

<dialog class="legend" id="legend" aria-labelledby="lg-title">
  <div class="lg-head">
    <h2 id="lg-title">Legend · Glossary</h2>
    <button class="lg-x" id="closeLegend" type="button">esc ✕</button>
  </div>
  <div class="lg-body">
    <section>
      <h3>Outcome — what a passing test proves</h3>
      <dl class="lg-defs">
        <dt><span class="pill out-TN">TN</span></dt>
        <dd>true-negative — good input <b>correctly allowed</b> (the happy path works).</dd>
        <dt><span class="pill out-TP">TP</span></dt>
        <dd>true-positive — invalid input + expect reject → <b>correctly blocked</b>.</dd>
        <dt><span class="pill out-FP">FP</span></dt>
        <dd>false-positive guard — valid edge input that might get wrongly blocked → must <b>not</b> be rejected.</dd>
        <dt><span class="pill out-FN">FN!</span></dt>
        <dd>false-negative guard — bad / attack input that might slip through → must <b>not</b> be accepted. <span class="caution">⚠ a breach if the control is missing.</span></dd>
      </dl>
    </section>
    <section>
      <h3>Type — what the case feeds</h3>
      <p class="lg-line"><code>POS</code> valid input expecting success &nbsp;·&nbsp; <code>NEG</code> invalid input expecting rejection &nbsp;·&nbsp; <code>VAPT</code> security / abuse input.</p>
    </section>
    <section>
      <h3>Priority — severity (two scales by case type)</h3>
      <table class="lg-tbl">
        <thead><tr><th>Functional (POS / NEG)</th><th>VAPT</th></tr></thead>
        <tbody><tr>
          <td><b>P0</b> blocker · <b>P1</b> major · <b>P2</b> minor</td>
          <td><b>CRIT</b> · <b>HIGH</b> · <b>MED</b> · <b>LOW</b></td>
        </tr></tbody>
      </table>
    </section>
    <section>
      <h3>Transition — state-machine move (From→To)</h3>
      <div class="lg-states">
        <div class="row2"><span class="tag">account</span><p class="lg-line"><code>A0</code> none(404) · <code>A1</code> unverified · <code>A2</code> active · <code>A3</code> suspended</p></div>
        <div class="row2"><span class="tag">card</span><p class="lg-line"><code>C0</code> not-found(404) · <code>C1</code> not-active · <code>C2</code> active-empty · <code>C3</code> active-funded · <code>C4</code> deactivated</p></div>
        <div class="row2"><span class="tag">forms</span><p class="lg-line"><code>A1→A2</code> a transition (verify moves unverified→active) · <code>C2/C3</code> applies in either state, no change · <code>A1×C3</code> a matrix cell (account A1 acting on a C3 card) · <code>—</code> not state-bound (most VAPT cases)</p></div>
      </div>
    </section>
    <div class="lg-caution"><span class="mk" aria-hidden="true">⚠</span><span><b class="ink">Caution.</b> <b>FN!</b> and <b>P0 / CRIT</b> rows are the security-critical guards — if the control is missing it is a <b>breach</b> (fund loss, account takeover, data exposure), not a cosmetic bug. Triage these first: they are 74 of the 135 cases.</span></div>
  </div>
</dialog>

<script>
const DATA = __DATA_JSON__;

const SEV = {
  P0:{tier:"crit",rank:0}, CRIT:{tier:"crit",rank:0},
  P1:{tier:"major",rank:1}, HIGH:{tier:"major",rank:1},
  P2:{tier:"minor",rank:2}, MED:{tier:"minor",rank:2},
  LOW:{tier:"low",rank:3},
};
const TIER_LABEL = {crit:"Critical", major:"Major", minor:"Minor", low:"Low"};
const SECTIONS = ["Account","Card-Activation","Card-Link","Top-Up","Redemption","Matrix","Deactivation","E2E","VAPT"];
const OUTCOMES = ["FN!","TP","TN","FP"];
const TIERS = ["crit","major","minor","low"];
const TYPES = ["POS","NEG","VAPT"];
const OUT_VAR = {"FN!":"--fn","TP":"--tp","TN":"--tn","FP":"--fp"};
const TIER_VAR = {crit:"--crit",major:"--major",minor:"--minor",low:"--low"};
const outClass = o => o === "FN!" ? "FN" : o;   // class-safe

// enrich
DATA.forEach(c=>{
  const s = SEV[c.priority] || {tier:"minor",rank:2};
  c._tier = s.tier; c._rank = s.rank;
  c._section = c.group.startsWith("VAPT") ? "VAPT" : c.group;
  c._hay = [c.id,c.title,c.steps,c.expected,c.why,c.transition,c.group,c.priority,c.outcome]
            .join(" ").toLowerCase();
});

const F = {section:new Set(), outcome:new Set(), tier:new Set(), type:new Set()};
let query = "", sortKey = "sev";

const $ = s => document.querySelector(s);
const listEl = $("#list"), countEl = $("#count"), clearEl = $("#clear");

// ── header stats ──
const total = DATA.length;
const fnN = DATA.filter(c=>c.outcome==="FN!").length;
const critN = DATA.filter(c=>c._rank===0).length;
$("#st-total").textContent = total;
$("#st-fn").textContent = fnN;
$("#st-crit").textContent = critN;
$("#srcline").textContent = __SUBTITLE_JS__ + " · " + total + " cases";
(function dist(){
  const order=["FN!","TP","TN","FP"];
  const el=$("#dist");
  order.forEach(o=>{
    const n=DATA.filter(c=>c.outcome===o).length;
    const s=document.createElement("span");
    s.className="s-"+outClass(o).toLowerCase();
    s.style.flex=n; s.title=o+": "+n; el.appendChild(s);
  });
})();

// ── facets ──
function countBy(pred){ return DATA.filter(pred).length; }
function buildChip(facet, value, label, n, extraClass="", swatchVar=null){
  const b=document.createElement("button");
  b.className="chip "+extraClass; b.type="button";
  b.setAttribute("aria-pressed","false");
  b.dataset.facet=facet; b.dataset.value=value;
  if(swatchVar){ const sw=document.createElement("span"); sw.className="swatch";
    sw.style.background="var("+swatchVar+")"; b.appendChild(sw); }
  b.insertAdjacentHTML("beforeend", label+' <span class="n">'+n+'</span>');
  b.addEventListener("click",()=>{
    const set=F[facet]; set.has(value)?set.delete(value):set.add(value);
    b.setAttribute("aria-pressed", set.has(value)?"true":"false");
    render();
  });
  return b;
}
function facetRow(lbl, nodes){
  const row=document.createElement("div"); row.className="facet";
  row.insertAdjacentHTML("beforeend",'<span class="lbl">'+lbl+'</span>');
  nodes.forEach(n=>row.appendChild(n)); return row;
}
(function buildFacets(){
  const host=$("#facets");
  host.appendChild(facetRow("section", SECTIONS.map(s=>
    buildChip("section",s,s,countBy(c=>c._section===s)))));
  host.appendChild(facetRow("outcome", OUTCOMES.map(o=>
    buildChip("outcome",o,o,countBy(c=>c.outcome===o),
      o==="FN!"?"c-fn":"","--"+ (OUT_VAR[o].slice(2)) ))));
  host.appendChild(facetRow("severity", TIERS.map(t=>
    buildChip("tier",t,TIER_LABEL[t],countBy(c=>c._tier===t),
      t==="crit"?"c-crit":"", TIER_VAR[t]))));
  host.appendChild(facetRow("type", TYPES.map(t=>
    buildChip("type",t,t,countBy(c=>c.type===t)))));
})();

// ── rows (built once, reused to preserve open state) ──
function pill(cls,txt){ return '<span class="pill '+cls+'">'+txt+'</span>'; }
function rowEl(c){
  const d=document.createElement("details"); d.className="row"; d.dataset.tier=c._tier; d.dataset.id=c.id;
  const trans = c.transition && c.transition!=="-" ? c.transition : "—";
  d.innerHTML =
    '<summary>'
      +'<span class="c-id">'+c.id+'</span>'
      +'<span class="c-meta">'
        +pill("sev-"+c._tier, c.priority)
        +pill("out-"+outClass(c.outcome), c.outcome)
        +'<span class="c-sec">'+c._section+'</span>'
      +'</span>'
      +'<span class="c-title">'+esc(c.title)+'</span>'
      +'<span class="caret" aria-hidden="true">›</span>'
    +'</summary>'
    +'<div class="detail"><div class="detail-in"><div class="detail-pad">'
      +'<dl>'
        +'<dt>class</dt><dd><span class="tagline">'
            +pill("sev-"+c._tier,c.priority+" · "+TIER_LABEL[c._tier])
            +pill("out-"+outClass(c.outcome),c.type+" / "+c.outcome)
            +'<span class="pill" style="color:var(--ink-2);border-color:var(--line-2)">'+c.group+'</span>'
          +'</span></dd>'
        +'<dt>transition</dt><dd class="mono">'+esc(trans)+'</dd>'
        +'<dt>steps · data</dt><dd>'+esc(c.steps)+'</dd>'
        +'<dt>expected</dt><dd>'+esc(c.expected)+'</dd>'
        +'<dt>why '+c.priority+'</dt><dd class="why" style="color:var('+TIER_VAR[c._tier]+')"><span style="color:var(--ink-2)">'+esc(c.why)+'</span></dd>'
      +'</dl>'
    +'</div></div></div>';
  return d;
}
function esc(s){ return String(s).replace(/[&<>]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[m])); }

const NODES = new Map(DATA.map(c=>[c.id, rowEl(c)]));

// ── render ──
const RANK_SECTION = Object.fromEntries(SECTIONS.map((s,i)=>[s,i]));
function passes(c){
  if(query && !c._hay.includes(query)) return false;
  if(F.section.size && !F.section.has(c._section)) return false;
  if(F.outcome.size && !F.outcome.has(c.outcome)) return false;
  if(F.tier.size && !F.tier.has(c._tier)) return false;
  if(F.type.size && !F.type.has(c.type)) return false;
  return true;
}
function sortCmp(a,b){
  if(sortKey==="id") return a.id.localeCompare(b.id,undefined,{numeric:true});
  if(sortKey==="section"){
    const s=RANK_SECTION[a._section]-RANK_SECTION[b._section];
    return s || a._rank-b._rank || a.id.localeCompare(b.id,undefined,{numeric:true});
  }
  return a._rank-b._rank || a.id.localeCompare(b.id,undefined,{numeric:true}); // sev
}
let firstPaint = true;
function render(){
  const matched = DATA.filter(passes).sort(sortCmp);
  const frag=document.createDocumentFragment();
  matched.forEach((c,i)=>{
    const n=NODES.get(c.id);
    if(firstPaint){ n.classList.add("enter"); n.style.setProperty("--d",(Math.min(i,26)*11)+"ms"); }
    frag.appendChild(n);
  });
  listEl.replaceChildren(frag);
  if(!matched.length){
    const e=document.createElement("div"); e.className="empty";
    e.innerHTML='<b>No cases match</b>Narrow your search or relax a filter.<br><button type="button">reset all</button>';
    e.querySelector("button").addEventListener("click",resetAll);
    listEl.appendChild(e);
  }
  const anyFilter = query || F.section.size||F.outcome.size||F.tier.size||F.type.size;
  countEl.innerHTML = "showing <b>"+matched.length+"</b> of "+total+" cases"+(anyFilter?" · filtered":"");
  clearEl.classList.toggle("show", !!anyFilter);
  firstPaint=false;
}
function resetAll(){
  query=""; $("#q").value="";
  Object.values(F).forEach(s=>s.clear());
  document.querySelectorAll('.chip[aria-pressed="true"]').forEach(c=>c.setAttribute("aria-pressed","false"));
  render();
}

// ── events ──
$("#q").addEventListener("input",e=>{ query=e.target.value.trim().toLowerCase(); render(); });
$("#sort").addEventListener("change",e=>{ sortKey=e.target.value; render(); });
clearEl.addEventListener("click",resetAll);

// ── legend dialog ──
const dlg = $("#legend");
$("#openLegend").addEventListener("click",()=>dlg.showModal());
$("#closeLegend").addEventListener("click",()=>dlg.close());
dlg.addEventListener("click",e=>{               // click on ::backdrop closes
  const r=dlg.getBoundingClientRect();
  if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) dlg.close();
});

document.addEventListener("keydown",e=>{
  const inQ = document.activeElement===$("#q");
  if(e.key==="/" && !inQ){ e.preventDefault(); $("#q").focus(); }
  else if(e.key==="?" && !inQ && !dlg.open){ e.preventDefault(); dlg.showModal(); }
  else if(e.key==="Escape" && inQ){
    if($("#q").value){ query=""; $("#q").value=""; render(); } else $("#q").blur();
  }
});

render();
</script>
</body>
</html>
"""

out = (HTML.replace("__TITLE__", html.escape(A.title))
           .replace("__SUBTITLE_JS__", json.dumps(A.subtitle))
           .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False)))
out_path.write_text(out, encoding="utf-8")
print("wrote %s (%d cases, %d KB)" % (out_path, len(data), len(out) // 1024))
