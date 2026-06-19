// Read the marketplace manifest and discover the skills each plugin ships.
//
// A plugin ships skills under plugins/<plugin>/skills/<skill>/SKILL.md. We parse
// just enough of each SKILL.md's YAML front-matter (name + description) to render
// the selection UI — no YAML dependency, the frontmatter here is flat key: value.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, "..");

/** Parse the leading `--- … ---` YAML front-matter into a flat {key: value} map. */
function parseFrontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  if (!m) return {};
  const out = {};
  let key = null;
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^([A-Za-z0-9_-]+):\s?(.*)$/);
    if (kv) {
      key = kv[1];
      out[key] = kv[2].trim();
    } else if (key && /^\s+/.test(line)) {
      // folded continuation of the previous value (e.g. a long description)
      out[key] = `${out[key]} ${line.trim()}`.trim();
    }
  }
  return out;
}

/** First sentence of a description, trimmed for a one-line hint. */
export function shortHint(desc, max = 96) {
  if (!desc) return "";
  const firstSentence = desc.split(/(?<=[.!?])\s/)[0] || desc;
  const s = firstSentence.replace(/\s+/g, " ").trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

/** Read .claude-plugin/marketplace.json. */
export function readMarketplace(repoRoot = REPO_ROOT) {
  const p = path.join(repoRoot, ".claude-plugin", "marketplace.json");
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

/** Absolute path to a plugin's directory from its manifest `source`. */
export function pluginDir(repoRoot, plugin) {
  const src = plugin.source || `./plugins/${plugin.name}`;
  return path.resolve(repoRoot, src);
}

/** Discover the skills a plugin ships: [{ name, description, dir }]. */
export function discoverSkills(repoRoot, plugin) {
  const skillsRoot = path.join(pluginDir(repoRoot, plugin), "skills");
  if (!fs.existsSync(skillsRoot)) return [];
  const out = [];
  for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const skillMd = path.join(skillsRoot, entry.name, "SKILL.md");
    if (!fs.existsSync(skillMd)) continue;
    const fm = parseFrontmatter(fs.readFileSync(skillMd, "utf8"));
    out.push({
      name: fm.name || entry.name,
      description: fm.description || "",
      dir: path.join(skillsRoot, entry.name),
    });
  }
  return out;
}
