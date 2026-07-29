#!/usr/bin/env node
/**
 * Builds docs/index.html — the dkv explainer.
 *
 * SOURCE OF TRUTH: this file. `docs/index.html` is generated and committed; never hand-edit
 * it. Run `node docs/build.mjs` after changing either this script or the plugin.
 *
 * The point of generating rather than hand-authoring: every number on the page is read from
 * the plugin or computed here. Contrast ratios are produced by shelling out to the plugin's
 * own `scripts/contrast.py`, so the page cannot disagree with the tool it documents. A page
 * whose figures are typed by hand drifts from the code the first time either changes.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SKILL = join(HERE, "..", "plugins", "dkv", "skills", "design-fundamentals");
const CONTRAST = join(SKILL, "scripts", "contrast.py");
const read = (p) => readFileSync(p, "utf8");

/* ─────────────────────────── 1. read the plugin ─────────────────────────── */

const REFS = ["color", "typography", "layout", "gestalt", "principles"];
const src = { skill: read(join(SKILL, "SKILL.md")) };
for (const r of REFS) src[r] = read(join(SKILL, "references", `${r}.md`));

/** Pull the ⚠ contested claims straight out of the references.
 *  Takes only the claim itself — the sentence after it is the rebuttal, which belongs
 *  in the reference file, not in a one-line list. */
function contested() {
  const out = [];
  for (const [file, text] of Object.entries(src)) {
    for (const m of text.matchAll(/⚠ \*\*contested(.*?)\*\*/gs)) {
      let label = m[1].replace(/^\s*[—-]\s*/, "").trim();
      label = label.replace(/^"/, "").replace(/[".]+$/, "").trim();
      // no quoted claim on the line (e.g. the 60/30/10 case) — take the first clause
      if (!label) {
        const after = text.slice(m.index + m[0].length, m.index + m[0].length + 160);
        label = after.replace(/^\s*[—-]\s*/, "").split(/[;.]/)[0].replace(/\s+/g, " ").trim();
      }
      if (label) out.push({ file: `${file}.md`, label });
    }
  }
  return out;
}

/** Gestalt strength ordering, from gestalt.md §11 — the page must not reorder it. */
function strengthOrder() {
  const sec = src.gestalt.split("## 11.")[1] || "";
  return [...sec.matchAll(/^\d\.\s+\*\*([^*]+)\*\*[^—]*—\s*(.+)$/gm)].map((m) => ({
    cue: m[1].trim(),
    note: m[2].trim().replace(/\s+/g, " "),
  }));
}

/** The scale ratios table from typography.md §4. */
function scaleRatios() {
  const rows = [...src.typography.matchAll(/^\|\s*\*?\*?([\d.]+)\*?\*?\s*\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|\s*([^|]+?)\s*\|$/gm)];
  return rows
    .filter((r) => !Number.isNaN(Number(r[1])))
    .map((r) => ({ ratio: Number(r[1]), name: r[2].trim(), character: r[3].trim() }));
}

const CONTESTED = contested();
const ORDER = strengthOrder();
const RATIOS = scaleRatios();

/* ─────────────────────────── 2. measure ─────────────────────────── */

/** Every ratio printed on the page comes through here — the plugin's own script. */
function ratio(fg, bg) {
  const out = execFileSync("python3", [CONTRAST, fg, bg], { encoding: "utf8" });
  return Number(out.trim().replace(/:1$/, ""));
}
function verdict(fg, bg, kind) {
  try {
    const out = execFileSync("python3", [CONTRAST, fg, bg, kind], { encoding: "utf8" });
    return { ratio: Number(out.match(/^([\d.]+):1/)[1]), pass: /pass/.test(out) };
  } catch (e) {
    const out = e.stdout.toString();
    return { ratio: Number(out.match(/^([\d.]+):1/)[1]), pass: false };
  }
}

/* OKLCH → sRGB so the palette is defined in the space impeccable asks for, but the
   figures can print real hex (and contrast.py can measure it). */
function oklchHex(L, C, H) {
  const h = (H * Math.PI) / 180, a = C * Math.cos(h), b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  const lin = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
  ];
  const f = (x) => { x = Math.min(1, Math.max(0, x)); return x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055; };
  return "#" + lin.map((v) => Math.round(f(v) * 255).toString(16).padStart(2, "0")).join("").toUpperCase();
}

const HUE = 20;
const T = {
  bg: "#FFFFFF", ink: "#191010", muted: "#675050", primary: "#C53443",
  deep: "#751E26", hair: "#DFD4D4", stroke: "#8D7B7B",
  dBg: "#130C0C", dInk: "#F4EFEE", dMuted: "#B29F9F", dPrimary: "#F46E6F",
  dHair: "#362B2A", dStroke: "#746564",
};

const M = {
  ink: ratio(T.ink, T.bg),
  muted: ratio(T.muted, T.bg),
  primary: ratio(T.primary, T.bg),
  stroke: verdict(T.stroke, T.bg, "ui"),
  hair: verdict(T.hair, T.bg, "ui"),
  dInk: ratio(T.dInk, T.dBg),
  dPrimary: ratio(T.dPrimary, T.dBg),
  dStroke: verdict(T.dStroke, T.dBg, "ui"),
};

/* Part 0 — one hue, three moves. Real values, computed. */
const HUE_BASE = oklchHex(0.55, 0.18, HUE);
const SWATCH = {
  hue:   { hex: HUE_BASE,                    label: "hue",   note: "pure colour" },
  tint:  { hex: oklchHex(0.80, 0.09, HUE),   label: "tint",  note: "+ white" },
  shade: { hex: oklchHex(0.33, 0.11, HUE),   label: "shade", note: "+ black" },
  tone:  { hex: oklchHex(0.55, 0.06, HUE),   label: "tone",  note: "+ grey" },
};
for (const k of Object.keys(SWATCH)) SWATCH[k].on = ratio(SWATCH[k].hex, T.bg);

/* Part 3 — the modular scale, computed from base 16. Must reproduce typography.md. */
const scaleSteps = (base, r, n) => Array.from({ length: n }, (_, i) => Math.round(base * r ** i));
const SCALE_125 = scaleSteps(16, 1.25, 6);   // typography.md: 16 → 20 → 25 → 31 → 39 → 49
const SCALE_PHI = scaleSteps(16, 1.618, 4);  // typography.md: 16 → 26 → 42 → 68

/* Part 1 — the two floors, demonstrated on the page's own tokens. */
const FLOORS = [
  { what: "body text",            token: "--ink",     fg: T.ink,     kind: "body", need: 4.5 },
  { what: "the accent, as text",  token: "--primary", fg: T.primary, kind: "body", need: 4.5 },
  { what: "figure strokes",       token: "--stroke",  fg: T.stroke,  kind: "ui",   need: 3.0 },
  { what: "decorative hairline",  token: "--hair",    fg: T.hair,    kind: "ui",   need: 3.0 },
].map((f) => ({ ...f, ...verdict(f.fg, T.bg, f.kind) }));

/* ─────────────────────────── 3. figures ─────────────────────────── */
/* Every figure: real <text>, <title>/<desc>, meaning never in colour alone, and a complete
   default state so a headless render or screenshot shows a finished page. Motion is added
   by a `data-play` attribute; without JS the figure simply sits at its end state. */

const fig = (id, title, desc, body, w = 720, h = 300) => `
<svg class="fig" id="${id}" viewBox="0 0 ${w} ${h}" role="img"
     aria-labelledby="${id}-t ${id}-d" preserveAspectRatio="xMidYMid meet">
  <title id="${id}-t">${title}</title>
  <desc id="${id}-d">${desc}</desc>
  ${body}
</svg>`;

/* ── Fig 0: hue → tint / shade / tone ── */
function fig0() {
  const order = ["tint", "hue", "tone", "shade"];
  const cells = order.map((k, i) => {
    const s = SWATCH[k], x = 60 + i * 155, isHue = k === "hue";
    return `
    <g class="sw" style="--i:${i}">
      <rect x="${x}" y="52" width="128" height="96" rx="2" fill="${s.hex}"
            stroke="${isHue ? "var(--ink)" : "var(--stroke)"}" stroke-width="${isHue ? 2 : 1}"/>
      ${isHue ? `<rect x="${x - 6}" y="46" width="140" height="108" rx="3" fill="none"
            stroke="var(--ink)" stroke-width="1" stroke-dasharray="3 3"/>` : ""}
      <text x="${x + 64}" y="176" class="lbl" text-anchor="middle">${s.label}</text>
      <text x="${x + 64}" y="194" class="num" text-anchor="middle">${s.hex}</text>
      <text x="${x + 64}" y="212" class="cap" text-anchor="middle">${s.note}</text>
    </g>`;
  }).join("");
  return fig("f0", "One hue and its three moves",
    `A single red hue at ${SWATCH.hue.hex}, marked with a dashed outline, sits between three colours derived from it: a tint at ${SWATCH.tint.hex} made by adding white, a tone at ${SWATCH.tone.hex} made by adding grey, and a shade at ${SWATCH.shade.hex} made by adding black.`,
    `<text x="60" y="32" class="cap">the dashed swatch is the hue — the other three are made from it</text>
     ${cells}`, 720, 232);
}

/* ── Fig 1: the two floors ── */
function fig1() {
  // log-ish scale 1..21 mapped across the plot
  const X = (r) => 70 + (Math.log(r) / Math.log(21)) * 560;
  const rows = FLOORS.map((f, i) => {
    const y = 84 + i * 44;
    const shape = f.pass
      ? `<circle cx="${X(f.ratio)}" cy="${y}" r="7" fill="var(--ink)"/>`
      : `<rect x="${X(f.ratio) - 6}" y="${y - 6}" width="12" height="12" fill="none"
               stroke="var(--ink)" stroke-width="2"/>
         <line x1="${X(f.ratio) - 6}" y1="${y - 6}" x2="${X(f.ratio) + 6}" y2="${y + 6}"
               stroke="var(--ink)" stroke-width="2"/>`;
    return `
    <g class="row" style="--i:${i}">
      <line x1="70" y1="${y}" x2="${X(f.ratio)}" y2="${y}" stroke="var(--stroke)" stroke-width="1"/>
      ${shape}
      ${X(f.ratio) > 470
        ? `<text x="${X(f.ratio) - 16}" y="${y + 4}" class="num" text-anchor="end">${f.ratio.toFixed(2)}:1</text>`
        : `<text x="${X(f.ratio) + 16}" y="${y + 4}" class="num">${f.ratio.toFixed(2)}:1</text>`}
      <text x="70" y="${y - 12}" class="lbl">${f.what} <tspan class="num">${f.token}</tspan></text>
      <text x="640" y="${y + 4}" class="cap" text-anchor="end">${f.pass ? "clears" : "below"} ${f.need}</text>
    </g>`;
  }).join("");
  const mark = (r, label, dy) => `
    <line x1="${X(r)}" y1="${60 - dy}" x2="${X(r)}" y2="262" stroke="var(--ink)" stroke-width="1" stroke-dasharray="2 4"/>
    <text x="${X(r)}" y="${52 - dy}" class="cap" text-anchor="middle">${label}</text>`;
  return fig("f1", "Two floors, not one",
    `A logarithmic contrast scale. Four of this page's own colours are plotted against two thresholds: 3.0 to 1 for non-text and 4.5 to 1 for body text. Body ink measures ${M.ink} to 1, the accent ${M.primary} to 1, figure strokes ${M.stroke.ratio} to 1, and the decorative hairline ${M.hair.ratio} to 1 — which is below both floors and is why it is only ever used for decoration.`,
    `${mark(3.0, "3.0 — non-text", 18)}${mark(4.5, "4.5 — body text", 0)}
     ${rows}
     <text x="70" y="286" class="cap">● clears its floor · ✕ below it — shape carries the verdict, not colour</text>`,
    720, 300);
}

/* ── Fig 2: schemes + 60/30/10 ── */
function fig2() {
  const cx = 150, cy = 130, rOuter = 84, rInner = 50;
  const seg = Array.from({ length: 12 }, (_, i) => {
    const a0 = (i * 30 - 90) * Math.PI / 180, a1 = ((i + 1) * 30 - 90) * Math.PI / 180;
    const hex = oklchHex(0.62, 0.15, i * 30);
    const p = (r, a) => `${(cx + r * Math.cos(a)).toFixed(1)} ${(cy + r * Math.sin(a)).toFixed(1)}`;
    return `<path d="M ${p(rInner, a0)} L ${p(rOuter, a0)} A ${rOuter} ${rOuter} 0 0 1 ${p(rOuter, a1)} L ${p(rInner, a1)} A ${rInner} ${rInner} 0 0 0 ${p(rInner, a0)} Z"
             fill="${hex}" stroke="var(--bg)" stroke-width="1"/>`;
  }).join("");
  const node = (i) => { const a = (i * 30 - 90 + 15) * Math.PI / 180; return `${cx + 67 * Math.cos(a)},${cy + 67 * Math.sin(a)}`; };
  const shapes = {
    complementary: [0, 6], analogous: [0, 1, 11], triadic: [0, 4, 8], square: [0, 3, 6, 9],
  };
  const polys = Object.entries(shapes).map(([name, idx], i) => `
    <g class="poly" data-scheme="${name}" ${i === 0 ? "" : 'opacity="0"'}>
      <polygon points="${idx.map(node).join(" ")}" fill="none" stroke="var(--ink)" stroke-width="2"/>
      ${idx.map((j) => { const [px, py] = node(j).split(","); return `<circle cx="${px}" cy="${py}" r="4.5" fill="var(--bg)" stroke="var(--ink)" stroke-width="2"/>`; }).join("")}
      <text x="${cx}" y="236" class="lbl" text-anchor="middle">${name}</text>
    </g>`).join("");
  const bar = [
    { pct: 60, label: "60 — dominant", fill: SWATCH.tint.hex },
    { pct: 30, label: "30 — secondary", fill: SWATCH.tone.hex },
    { pct: 10, label: "10 — accent", fill: SWATCH.hue.hex },
  ];
  let x = 300;
  const bars = bar.map((b, i) => {
    const w = (b.pct / 100) * 360, r = `<g class="bar" style="--i:${i}">
      <rect x="${x}" y="92" width="${w}" height="52" fill="${b.fill}" stroke="var(--stroke)" stroke-width="1"/>
      <text x="${x + 6}" y="164" class="cap">${b.label}</text></g>`;
    x += w; return r;
  }).join("");
  return fig("f2", "Schemes are shapes on the wheel; proportion is separate",
    `A twelve-segment colour wheel with a polygon showing which hues a scheme selects — complementary picks two opposite, analogous picks neighbours, triadic a triangle, square four evenly spaced. Beside it, a bar divided sixty, thirty and ten percent showing how much of each colour is used. The scheme decides which hues; the proportion decides how much.`,
    `<text x="60" y="32" class="cap">which hues — a shape you rotate</text>
     <text x="300" y="32" class="cap">how much of each — a separate decision</text>
     ${seg}${polys}
     ${bars}
     <text x="300" y="196" class="cap">⚠ 60/30/10 is a studio heuristic, not a finding — a starting proportion to deviate from</text>`,
    720, 252);
}

/* ── Fig 3: the modular scale ── */
function fig3() {
  const ladder = (steps, x, label, note, flag) => {
    const bars = steps.map((s, i) => `
      <g class="step" style="--i:${i}">
        <rect x="${x}" y="${64 + i * 34}" width="${s * 2.6}" height="22" fill="var(--primary)" opacity="0.16"
              stroke="var(--stroke)" stroke-width="1"/>
        <text x="${x + 8}" y="${80 + i * 34}" class="num">${s}px</text>
      </g>`).join("");
    return `<text x="${x}" y="40" class="lbl">${label}</text>
            <text x="${x}" y="56" class="cap">${note}</text>${bars}
            ${flag ? `<text x="${x}" y="${64 + steps.length * 34 + 16}" class="cap">${flag}</text>` : ""}`;
  };
  return fig("f3", "A scale is a ratio you commit to",
    `Two type scales built from a 16 pixel base. At a 1.25 ratio the sizes run ${SCALE_125.join(", ")} pixels — six usable steps. At the golden ratio of 1.618 they run ${SCALE_PHI.join(", ")} pixels and reach an unusable size after only four, which is why it suits posters rather than interfaces.`,
    `${ladder(SCALE_125, 60, "ratio 1.25 — major third", "comfortable default, six usable steps", "")}
     ${ladder(SCALE_PHI, 400, "ratio 1.618 — golden ratio", "dramatic; runs out after four", "⚠ φ is a usable ratio, not a law of beauty")}`,
    720, 300);
}

/* ── Fig 4: measure ── */
function fig4() {
  const band = (from, to) => `
    <rect x="${60 + from * 6.4}" y="60" width="${(to - from) * 6.4}" height="150" fill="var(--primary)" opacity="0.08"/>
    <line x1="${60 + from * 6.4}" y1="52" x2="${60 + from * 6.4}" y2="216" stroke="var(--ink)" stroke-width="1" stroke-dasharray="2 4"/>
    <line x1="${60 + to * 6.4}" y1="52" x2="${60 + to * 6.4}" y2="216" stroke="var(--ink)" stroke-width="1" stroke-dasharray="2 4"/>
    <text x="${60 + from * 6.4}" y="44" class="cap" text-anchor="middle">45ch</text>
    <text x="${60 + to * 6.4}" y="44" class="cap" text-anchor="middle">75ch</text>`;
  const lines = Array.from({ length: 6 }, (_, i) => `
    <rect class="ln" style="--i:${i}" x="72" y="${72 + i * 22}" height="8" rx="1" width="380" fill="var(--stroke)" opacity="0.5"/>`).join("");
  return fig("f4", "Measure is counted in characters, not pixels",
    `A column of text with the comfortable band between 45 and 75 characters per line marked. Lines shorter than the band break the reading rhythm every few words; longer than it, the eye loses its place returning to the next line. Around 66 characters is the usual optimum.`,
    `${band(45, 75)}${lines}
     <text x="60" y="238" class="cap">shorter — rhythm breaks every few words</text>
     <text x="660" y="238" class="cap" text-anchor="end">longer — the eye loses the return sweep</text>
     <text x="60" y="24" class="lbl">the band is 45–75 characters · this page's body column sits inside it</text>`,
    720, 250);
}

/* ── Fig 5: gestalt strength ordering — the centrepiece ── */
function fig5() {
  const marks = (n = 6) => Array.from({ length: n }, (_, i) => i);
  const stage = (idx, title, note, render) => `
    <g class="stage" data-stage="${idx}" style="--i:${idx}">
      <text x="60" y="${44 + idx * 76}" class="lbl">${idx + 1}. ${title}</text>
      <text x="60" y="${60 + idx * 76}" class="cap">${note}</text>
      ${render(84 + idx * 76)}
    </g>`;
  const dot = (x, y, filled) => filled
    ? `<circle cx="${x}" cy="${y}" r="9" fill="var(--primary)"/>`
    : `<circle cx="${x}" cy="${y}" r="9" fill="none" stroke="var(--ink)" stroke-width="2"/>`;
  const s1 = (y) => marks().map((i) => dot(330 + i * 40, y, i < 3)).join("");
  const s2 = (y) => marks().map((i) => dot(330 + i * 40 + (i < 3 ? 0 : 34), y, i < 3)).join("");
  const s3 = (y) => `<rect x="314" y="${y - 20}" width="155" height="40" rx="3" fill="none"
        stroke="var(--ink)" stroke-width="1.5"/>` + marks().map((i) => dot(330 + i * 40, y, i < 3)).join("");
  const s4 = (y) => `<line x1="330" y1="${y}" x2="530" y2="${y}" stroke="var(--ink)" stroke-width="2"/>`
        + marks().map((i) => dot(330 + i * 40, y, i < 3)).join("");
  return fig("f5", "Which grouping cue wins",
    `Six marks, three filled and three hollow, shown four times. With similarity alone the filled and hollow marks group by appearance. Adding a gap regroups them by position, overriding appearance. Drawing a box around the first four regroups them again, overriding the gap. Finally a line connecting five of them overrides everything — a connector is the strongest cue, and shared styling is the weakest.`,
    `${stage(0, ORDER[3] ? ORDER[3].cue : "Similarity", "shared styling — the weakest cue", s1)}
     ${stage(1, ORDER[2] ? ORDER[2].cue : "Proximity", "space overrides appearance", s2)}
     ${stage(2, ORDER[1] ? ORDER[1].cue : "Common region", "a container overrides space", s3)}
     ${stage(3, ORDER[0] ? ORDER[0].cue : "Uniform connectedness", "a connector overrides all of it", s4)}
     <text x="60" y="352" class="cap">read downward: each row overrides the one above it</text>`,
    720, 366);
}

/* ── Fig 6: hierarchy, built from the scale ── */
function fig6() {
  const [, s20, s25, s31, s39, s49] = SCALE_125;
  const rows = [
    { size: s49, w: 300, role: "headline", step: `${s49}px` },
    { size: s31, w: 220, role: "subhead", step: `${s31}px` },
    { size: s20, w: 340, role: "body", step: `${s20}px` },
    { size: s20, w: 300, role: "body", step: "" },
    { size: 16, w: 150, role: "caption", step: "16px" },
  ];
  let y = 70;
  const bars = rows.map((r, i) => {
    const h = Math.max(6, r.size * 0.34);
    const g = `<g class="hrow" style="--i:${i}">
      <rect x="60" y="${y}" width="${r.w}" height="${h}" fill="var(--ink)" opacity="${i === 0 ? 1 : i < 3 ? 0.75 : 0.45}"/>
      ${r.step ? `<text x="${60 + r.w + 12}" y="${y + h - 1}" class="num">${r.step}</text>` : ""}
      ${r.step ? `<text x="470" y="${y + h - 1}" class="cap">${r.role}</text>` : ""}
    </g>`;
    y += h + 16; return g;
  }).join("");
  return fig("f6", "Hierarchy is the scale, applied",
    `Five blocks of decreasing size standing in for a headline at ${s49} pixels, a subhead at ${s31}, two lines of body at ${s20}, and a caption at 16. Each size is a step on the same 1.25 scale, so the difference between levels is deliberate rather than picked by eye.`,
    `<text x="60" y="40" class="cap">every size is a step on the 1.25 ladder from Part 3 — none picked by eye</text>${bars}`,
    720, y + 20);
}

/* ── Fig 7: the review pass ── */
function fig7() {
  const steps = [...src.skill.matchAll(/^\d\.\s+\*\*([^*]+)\*\*\s*—/gm)]
    .map((m) => m[1].trim()).slice(-7);
  const rows = steps.map((s, i) => `
    <g class="chk" style="--i:${i}">
      <line x1="60" y1="${58 + i * 32}" x2="660" y2="${58 + i * 32}" stroke="var(--hair)" stroke-width="1"/>
      <text x="60" y="${52 + i * 32}" class="lbl">${i + 1}. ${s}</text>
      <circle cx="646" cy="${47 + i * 32}" r="5" fill="var(--ink)"/>
    </g>`).join("");
  return fig("f7", "The review pass, in order",
    `The seven checks the skill runs over a design, in order: ${steps.join("; ")}. The order is deliberate — the cheapest and most objective checks run first, so a beautiful but unreadable design is caught before anyone argues about taste.`,
    `<text x="60" y="28" class="cap">cheapest and most objective first — the legibility floor is pass/fail, not preference</text>${rows}`,
    720, 58 + steps.length * 32);
}

/* ─────────────────────────── 4. page ─────────────────────────── */

const PARTS = [
  { n: 0, term: "hue", title: "A colour, and the three things you can do to it",
    fig: fig0(),
    body: `<p>Everything else on this page is built from this one idea, so it comes first.</p>
    <p>A <b>hue</b> is a pure colour — red, blue, green — with nothing added. It is the raw material. Every other colour in a palette is a hue that has been moved in one of exactly three directions: add white and you get a <b>tint</b>, which feels lighter and airier. Add black and you get a <b>shade</b>, heavier and denser. Add grey and you get a <b>tone</b>, which is the same colour with the shouting taken out.</p>
    <p>This matters more than it sounds. Palettes that feel amateurish are usually made of pure hues at full strength, all competing at the same volume. Tints, shades and tones are what give you a <em>quiet</em> colour — something you can put across most of a page without it fighting everything else.</p>` },

  { n: 1, term: "contrast ratio", title: "Two colours make a number, and the number has two floors",
    fig: fig1(),
    body: `<p>Put any two colours together and the difference between them can be measured. That measurement is a <b>contrast ratio</b>, written like <span class="n">4.5:1</span>. Identical colours are <span class="n">1:1</span>; black on white is the maximum, <span class="n">21:1</span>. It is arithmetic, not opinion — which makes it the one part of design review nobody can argue with.</p>
    <p>There are two thresholds, and the second is the one almost everyone forgets. Body text needs <b>4.5:1</b> against its background. But <em>non-text</em> also needs <b>3:1</b> — the border of a button, a focus ring, an icon, the stroke of a chart. Anything a reader must see to understand what they are looking at.</p>
    <p>The failure this catches is specific and common: a button whose label sits at a comfortable 13:1 while its border sits at 2:1. The text is perfectly readable. The thing telling you it is a button is not.</p>
    <p>The plot above is this page measuring itself. The hairline used for decorative rules lands at <span class="n">${M.hair.ratio}:1</span> — far below both floors — which is exactly why it is never used to draw anything you need to see. Figure strokes use a different token at <span class="n">${M.stroke.ratio}:1</span>.</p>` },

  { n: 2, term: "scheme", title: "Which colours, and how much of each",
    fig: fig2(),
    body: `<p>Arrange every hue in a circle and the schemes become shapes you rotate. <b>Complementary</b> takes two hues opposite each other — the loudest pairing available. <b>Analogous</b> takes two or three neighbours, which is calm and hard to get wrong. <b>Triadic</b> takes a triangle. Rotate any of these shapes and you get a different palette with identical structure.</p>
    <p>But a scheme only tells you <em>which</em> colours, never <em>how much</em> of each — and that second decision is where palettes usually fail. The common starting point is <b>60/30/10</b>: sixty percent of the surface in a dominant colour, thirty in a secondary, ten in an accent. The part people get wrong is that the meaningful contrast belongs between the 60 and the 30. If those two are nearly identical, the layout reads flat no matter how loud the accent is.</p>
    <p class="flag">⚠ 60/30/10 comes from interior design and has no empirical basis — practitioners describe it as an old rule of thumb. It is genuinely useful as a starting proportion, because it stops you splitting a canvas evenly three ways, which almost never works. It is a default to deviate from deliberately, not a law.</p>` },

  { n: 3, term: "modular scale", title: "Type sizes should come from a ratio, not from taste",
    fig: fig3(),
    body: `<p>Pick a base size and one ratio, then multiply repeatedly. That is a <b>modular scale</b>, and it is the difference between a type system that looks deliberate and one that looks assembled. From a 16px base at a ratio of 1.25 you get <span class="n">${SCALE_125.join(" · ")}</span>. Every size is visibly related to every other because they share a common origin.</p>
    <p>The ratio is a real choice. Small ratios like 1.125 give tight, dense steps suited to interfaces. Larger ones are dramatic and run out of usable sizes quickly.</p>
    <p class="flag">⚠ The golden ratio, φ ≈ 1.618, is a perfectly good scale ratio — and it is not a law of beauty. That claim was popularised by Adolf Zeising in the 1850s; its empirical basis was Fechner's 1876 rectangle experiments, and the replications did not hold — Godkewitsch (1974) and Green's 1995 review found the preference disappears once stimulus range and context are controlled. What survives is a mild preference for a broad band of ratios roughly between 1.4 and 1.8, within which 1.618 is not special. Use it because it produces a strong dramatic step, not because it is magic. From 16px it gives <span class="n">${SCALE_PHI.join(" · ")}</span> — four usable steps, which is why it suits a poster more than an interface.</p>` },

  { n: 4, term: "measure", title: "Line length is counted in characters",
    fig: fig4(),
    body: `<p><b>Measure</b> is the length of a line of text, counted in characters rather than pixels — because what matters is how many words the eye crosses, not how wide the column is. The comfortable band for body text is <b>45 to 75 characters</b>, with around 66 the usual optimum. On screen, 40 to 60 also works.</p>
    <p>Both ends fail in their own way. Too short and the reading rhythm breaks every few words. Too long and the eye loses its place on the return sweep to the next line — you re-read a line, or skip one, and stop trusting the text.</p>
    <p><b>Leading</b> — the vertical space between lines — moves with it. Body text wants 120 to 150 percent of its size, and the longer the measure, the more leading it needs to keep the eye on the right line. Headlines go tighter, 1.0 to 1.2, because large type already has plenty of air.</p>` },

  { n: 5, term: "grouping cues", title: "The eye groups things before it reads them",
    fig: fig5(),
    body: `<p>Before anyone reads a word, their eye has already sorted the page into groups. Whatever your layout groups <em>visually</em> is the meaning the reader receives — regardless of what the content actually says. There are several cues that do this grouping, and crucially <b>they are not equal in strength</b>.</p>
    <p>Weakest is <b>similarity</b>: things that look alike are read as related. Stronger is <b>proximity</b>: things placed near each other are read as related, and this beats appearance. Stronger still is <b>common region</b>: a shared box or background groups whatever is inside it, whatever the spacing. Strongest of all is <b>uniform connectedness</b>: a visible connector — a line, a rule, a bar — beats everything else, and it does not even need to touch the elements.</p>
    <p>This ordering is the practically useful part. If two things must read as related but sit far apart, styling them alike is the <em>weakest</em> available fix — connect them or contain them instead. And when a grouping looks wrong although every element is styled correctly, look for an accidental box or line overriding your intent before touching the styling.</p>` },

  { n: 6, term: "hierarchy", title: "Putting it together: what gets seen first",
    fig: fig6(),
    body: `<p><b>Hierarchy</b> is the order in which a reader receives things. It is built from the previous parts: sizes from the scale, contrast from the ratio, grouping from the cues. Size and weight and contrast all push an element up or down the order, and used together they make the sequence unmistakable.</p>
    <p>The commonest failure is promoting everything. When three elements are all the most important, none of them is. The working test: if you cannot name the single most important element in the composition, neither can the reader.</p>` },

  { n: 7, term: "the review pass", title: "Reading a design back",
    fig: fig7(),
    body: `<p>With every term defined, the checks can run in order. The sequence is deliberate — the objective, pass/fail checks come first, so a beautiful but unreadable design is caught before anyone starts arguing about taste. Only then does judgement enter.</p>
    <p>A critique that lists fifteen equal-weight findings does not get acted on. The output that matters is two or three highest-impact fixes, each naming the principle it comes from and the specific change to make.</p>
    <h3>What it refuses to claim</h3>
    <p>Four claims in wide circulation are marked contested rather than repeated, because design advice that states folklore confidently is the exact failure this method exists to avoid:</p>
    <ul class="claims">${CONTESTED.map((c) => `<li><span class="n">${c.file}</span> ${c.label}</li>`).join("")}</ul>
    <h3>Where it stops</h3>
    <p>This method covers <b>print and static graphic design</b> — posters, packaging, labels, menus, signage, book covers, logos, slide decks, social posts. It does not cover websites, app or product interfaces, dashboards or components; those have their own constraints — interaction states, responsive behaviour, focus order — that a static review will not surface. It does not cover motion design, and it does not generate images. Knowing where a method stops is part of using it honestly.</p>` },
];

const css = `
:root{
  color-scheme: light dark;
  --bg:${T.bg}; --ink:${T.ink}; --muted:${T.muted}; --primary:${T.primary};
  --deep:${T.deep}; --hair:${T.hair}; --stroke:${T.stroke};
  --measure: 68ch;
  --s1:8px; --s2:16px; --s3:24px; --s4:32px; --s5:48px; --s6:64px; --s7:96px;
  --ease-out: cubic-bezier(.23,1,.32,1);
  --ease-in-out: cubic-bezier(.77,0,.175,1);
  --z-fig:1; --z-nav:10;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:${T.dBg}; --ink:${T.dInk}; --muted:${T.dMuted}; --primary:${T.dPrimary};
         --deep:${T.dPrimary}; --hair:${T.dHair}; --stroke:${T.dStroke}; }
}
*,*::before,*::after{ box-sizing:border-box; }
html{ -webkit-text-size-adjust:100%; }
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size:${SCALE_125[1]}px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.n, .num{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size:.88em; font-variant-numeric: tabular-nums; letter-spacing:-.01em; }

/* proof-sheet chrome: registration marks at the corners of the sheet */
.sheet{ position:relative; max-width:1180px; margin:0 auto; padding:var(--s6) var(--s4) var(--s7); }
.reg{ position:absolute; width:22px; height:22px; opacity:.55; }
.reg.tl{ top:18px; left:14px } .reg.tr{ top:18px; right:14px }
.reg.bl{ bottom:18px; left:14px } .reg.br{ bottom:18px; right:14px }

header.mast{ border-bottom:2px solid var(--ink); padding-bottom:var(--s3); margin-bottom:var(--s2); }
.mast h1{
  font-size: clamp(2.2rem, 1.2rem + 4vw, 4.2rem); line-height:1.03;
  letter-spacing:-.035em; margin:0 0 var(--s2); text-wrap:balance; font-weight:640;
}
.mast .sub{ max-width:var(--measure); color:var(--ink); margin:0 0 var(--s3); text-wrap:pretty; }
.mast dl{ display:flex; flex-wrap:wrap; gap:var(--s2) var(--s5); margin:0; font-size:.86rem; }
.mast .pair{ display:flex; align-items:baseline; gap:var(--s1); }
.mast dt{ color:var(--muted); margin:0; } .mast dd{ margin:0; }

.part{ padding:var(--s5) 0 var(--s6); border-top:1px solid var(--hair); }
.part:first-of-type{ border-top:0; }
.part-head{ display:flex; align-items:baseline; gap:var(--s3); margin-bottom:var(--s2); }
.part-n{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.8rem;
  border:1px solid var(--stroke); padding:2px 8px; color:var(--ink); flex:none;
}
.part h2{ font-size: clamp(1.4rem, 1.1rem + 1.2vw, 2.1rem); line-height:1.15;
  letter-spacing:-.02em; margin:0; text-wrap:balance; font-weight:620; }
.term{ color:var(--muted); font-size:.86rem; margin:0 0 var(--s3); }
.term b{ color:var(--primary); font-weight:600; }
.prose{ max-width:var(--measure); }
.prose p{ margin:0 0 var(--s3); text-wrap:pretty; }
.prose h3{ font-size:1.05rem; margin:var(--s5) 0 var(--s2); letter-spacing:-.01em; }
.prose b{ font-weight:640; }
.flag{ border:1px solid var(--stroke); padding:var(--s3); background:transparent; }
.claims{ max-width:var(--measure); padding-left:1.1em; margin:0 0 var(--s3); }
.claims li{ margin-bottom:var(--s1); }

figure{ margin:0 0 var(--s4); }
.figwrap{ border:1px solid var(--hair); padding:var(--s3) var(--s2); position:relative; }
/* Below ~700px the 720-unit viewBox would scale figure text down to ~5px. Give the
   figure a floor and let it scroll inside its own box: legibility wins, and the page
   itself still never scrolls horizontally. */
.figscroll{ overflow-x:auto; overscroll-behavior-x:contain; }
.figscroll svg.fig{ min-width:640px; }
svg.fig{ display:block; width:100%; max-width:820px; margin:0 auto; height:auto; overflow:visible; }
svg .lbl{ font-family:inherit; font-size:13px; fill:var(--ink); font-weight:600; }
svg .cap{ font-family:inherit; font-size:11.5px; fill:var(--muted); }
svg .num{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12px;
  fill:var(--ink); font-variant-numeric:tabular-nums; }
figcaption{ font-size:.82rem; color:var(--muted); margin-top:var(--s2); max-width:var(--measure); }

.replay{
  position:absolute; top:6px; right:6px; z-index:var(--z-fig); font:inherit; font-size:.78rem;
  background:var(--bg); color:var(--ink); border:1px solid var(--stroke);
  min-height:44px; min-width:44px; padding:0 14px; cursor:pointer;
  transition: transform 160ms var(--ease-out), border-color 160ms var(--ease-out);
}
.replay:hover{ border-color:var(--ink); }
.replay:active{ transform:scale(.97); }
.replay:focus-visible{ outline:2px solid var(--primary); outline-offset:2px; }

footer{ border-top:2px solid var(--ink); margin-top:var(--s6); padding-top:var(--s3);
  color:var(--muted); font-size:.86rem; max-width:var(--measure); }
footer a{ color:var(--primary); }
a{ color:var(--primary); text-underline-offset:2px; }

/* ── motion ───────────────────────────────────────────────────────────────
   ARCHITECTURE: the default state of every figure is its FINAL state. Motion is a
   transition *out of* a start state and back, applied only while [data-from] is set
   for one frame by JS. Keyframes with a backwards fill were the first attempt and were
   wrong: through the stagger delay they hold elements at opacity 0, so a screenshot or
   a fast headless snapshot catches a blank figure. With this structure, no-JS,
   hidden-tab and mid-render all show a complete page. */
.sw, .row, .bar, .step, .ln, .stage, .hrow, .chk{
  opacity:1; transform:none;
  transition: opacity 520ms var(--ease-out), transform 520ms var(--ease-out);
  transition-delay: calc(var(--i, 0) * 80ms);
}
[data-from] .sw, [data-from] .row, [data-from] .bar, [data-from] .step,
[data-from] .ln, [data-from] .stage, [data-from] .hrow, [data-from] .chk{
  transition:none;
}
[data-from] .sw{ opacity:0; transform: translateY(10px); }
[data-from] .row, [data-from] .bar, [data-from] .step,
[data-from] .ln, [data-from] .hrow{ opacity:0; transform: translateX(-14px); }
[data-from] .stage{ opacity:0; transform: translateX(-16px); }
[data-from] .chk{ opacity:0; transform: translateY(7px); }

/* the scheme polygons cycle rather than enter — they are the teaching in Part 2 */
.poly{ transition: opacity 420ms var(--ease-in-out); }
[data-play] .poly{ animation: polyCycle 6400ms linear infinite both; }
@keyframes polyCycle{ 0%,20%{opacity:1} 25%,95%{opacity:0} 100%{opacity:1} }
[data-play] .poly[data-scheme="analogous"]{ animation-delay:1600ms }
[data-play] .poly[data-scheme="triadic"]{ animation-delay:3200ms }
[data-play] .poly[data-scheme="square"]{ animation-delay:4800ms }

@media (prefers-reduced-motion: reduce){
  /* No transform motion at all. Figures are already complete, so the reduced-motion
     alternative is simply the finished figure — plus a crossfade on replay. */
  .sw, .row, .bar, .step, .ln, .stage, .hrow, .chk{
    transition: opacity 200ms ease; transition-delay:0ms !important; transform:none !important;
  }
  [data-from] .sw, [data-from] .row, [data-from] .bar, [data-from] .step,
  [data-from] .ln, [data-from] .stage, [data-from] .hrow, [data-from] .chk{
    opacity:.4; transform:none !important;
  }
  [data-play] .poly{ animation:none; }
  .poly:not([data-scheme="complementary"]){ opacity:0; }
  .poly[data-scheme="complementary"]{ opacity:1; }
}
@media (max-width: 640px){
  .sheet{ padding:var(--s5) var(--s3) var(--s6); }
  .part{ padding:var(--s5) 0; }
  .part-head{ flex-direction:column; gap:var(--s1); }
  .figwrap{ padding:var(--s2) var(--s1); }
  .reg{ display:none; }
}`;

const js = `
// Figures are already complete when this runs. It only replays the teaching motion by
// pushing each figure into its start state for a single frame, then releasing it.
(function(){
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  function play(el){
    el.setAttribute('data-from','');
    void el.offsetWidth;                     // commit the start state
    requestAnimationFrame(function(){
      requestAnimationFrame(function(){ el.removeAttribute('data-from'); });
    });
  }
  var wraps = Array.prototype.slice.call(document.querySelectorAll('.figwrap'));
  wraps.forEach(function(w){
    var btn = w.querySelector('.replay');
    if (btn) btn.addEventListener('click', function(){ play(w); });
    if (w.querySelector('.poly')) w.setAttribute('data-play','');   // Part 2 cycles
  });
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting && !e.target.dataset.seen){
        e.target.dataset.seen = '1';
        if (!reduce.matches) play(e.target);
      }
    });
  }, { threshold: 0.3 });
  wraps.forEach(function(w){ io.observe(w); });
})();`;

const regMark = (cls) => `<svg class="reg ${cls}" viewBox="0 0 22 22" aria-hidden="true">
  <line x1="11" y1="0" x2="11" y2="22" stroke="${T.stroke}" stroke-width="1"/>
  <line x1="0" y1="11" x2="22" y2="11" stroke="${T.stroke}" stroke-width="1"/>
  <circle cx="11" cy="11" r="6" fill="none" stroke="${T.stroke}" stroke-width="1"/></svg>`;

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dkv — reading a design back</title>
<meta name="description" content="How the dkv plugin reviews graphic design: eight terms, each built from the last, every number measured rather than illustrated.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='9' fill='none' stroke='%23C53443' stroke-width='2.5'/%3E%3Cpath d='M16 1v30M1 16h30' stroke='%23C53443' stroke-width='2.5'/%3E%3C/svg%3E">
<!-- Generated by docs/build.mjs — do not hand-edit. Register: docs/PRODUCT.md -->
<style>${css}</style>
</head>
<body>
<main class="sheet">
${regMark("tl")}${regMark("tr")}${regMark("bl")}${regMark("br")}

<header class="mast">
  <h1>Reading a design back</h1>
  <p class="sub"><b>dkv</b> is a design-review method: eight terms, each one built from the term before it, ending in a pass you can run over your own work. Every number here was measured — the contrast ratios come from the plugin's own <span class="n">contrast.py</span>, the type sizes from its scale. Nothing is illustrative.</p>
  <dl>
    <div class="pair"><dt>Covers</dt><dd>print &amp; static graphics</dd></div>
    <div class="pair"><dt>Body text</dt><dd class="n">${M.ink}:1</dd></div>
    <div class="pair"><dt>Measure</dt><dd class="n">\u2264 68ch</dd></div>
    <div class="pair"><dt>Scale</dt><dd class="n">16px × 1.25</dd></div>
  </dl>
</header>

${PARTS.map((p) => `
<section class="part" id="part-${p.n}" aria-labelledby="h-${p.n}">
  <div class="part-head">
    <span class="part-n" aria-hidden="true">PART ${p.n}</span>
    <h2 id="h-${p.n}">${p.title}</h2>
  </div>
  <p class="term">defines <b>${p.term}</b>${p.n > 0 ? ` · built on ${PARTS[p.n - 1].term}` : " · needs nothing before it"}</p>
  <figure>
    <div class="figwrap">
      <button class="replay" type="button">replay</button>
      <div class="figscroll">${p.fig}</div>
    </div>
  </figure>
  <div class="prose">${p.body}</div>
</section>`).join("")}

<footer>
  <p>The parts are numbered because they are a sequence — each is built from the term the one before it defined. Generated from <span class="n">docs/build.mjs</span>, which reads the plugin at <span class="n">plugins/dkv/</span>; the ratios are produced by running <span class="n">scripts/contrast.py</span> at build time, so this page cannot disagree with the tool it documents.</p>
  <p><a href="https://github.com/labspangaea/pangaealabs-claude-plugins-marketplace">pangaealabs-claude-plugins-marketplace</a> · <span class="n">/plugin install dkv@pangaealabs-claude-plugins-marketplace</span></p>
</footer>
</main>
<script>${js}</script>
</body>
</html>`;

writeFileSync(join(HERE, "index.html"), html);

console.log("built docs/index.html");
console.log(`  parts        ${PARTS.length}`);
console.log(`  contested    ${CONTESTED.length} (${CONTESTED.map((c) => c.file).join(", ")})`);
console.log(`  cues (§11)   ${ORDER.length ? ORDER.map((o) => o.cue).join(" > ") : "NONE PARSED — check gestalt.md §11"}`);
console.log(`  ratios       ${RATIOS.length} parsed from typography.md`);
console.log(`  scale 1.25   ${SCALE_125.join(" ")}`);
console.log(`  scale phi    ${SCALE_PHI.join(" ")}`);
console.log(`  measured     ink ${M.ink}:1 · primary ${M.primary}:1 · stroke ${M.stroke.ratio}:1 (${M.stroke.pass ? "pass" : "FAIL"}) · hair ${M.hair.ratio}:1 (decorative)`);
