// Install engine: assemble a relocatable skill bundle, place it in the universal
// store, and link it into each selected agent's skills dir.
//
// Why "relocatable": docsmith's make-pdf SKILL.md leans on sibling support dirs
// (scripts/, assets/, references/) that live at the PLUGIN root, not inside the
// skill folder. build.py resolves its plugin root as `Path(__file__).parent.parent`
// — i.e. the dir that contains scripts/. So if we lay the bundle out as
// <skill>/{scripts,assets,references} (mirroring the plugin), build.py works
// UNCHANGED from the relocated location. We copy exactly those support dirs plus
// the skill's own files; plugin-only bits (monitors/, agents/, evals/) are left
// behind because they're Claude-Code-plugin machinery, inert in a bare skill.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { storeDir, agentSkillsDir } from "./agents.mjs";

// Plugin support dirs copied into every skill bundle (when present).
const SUPPORT_DIRS = ["scripts", "assets", "references"];
// Individual support files worth carrying (relative to the plugin dir).
const SUPPORT_FILES = ["examples/profile.example.yaml"];

const PRUNE = new Set(["__pycache__", ".DS_Store"]);

function copyTree(src, dest) {
  fs.cpSync(src, dest, {
    recursive: true,
    filter: (s) => {
      const base = path.basename(s);
      return !PRUNE.has(base) && !base.endsWith(".pyc");
    },
  });
}

/** Collapse $HOME → ~ for display. */
export function displayPath(p, home = os.homedir()) {
  return p.startsWith(home) ? p.replace(home, "~") : p;
}

/** Assemble the relocatable bundle for one skill into `destSkillDir`. */
export function assembleBundle(pluginDirPath, skill, destSkillDir) {
  fs.mkdirSync(destSkillDir, { recursive: true });
  // 1) plugin-shared support dirs first …
  for (const d of SUPPORT_DIRS) {
    const src = path.join(pluginDirPath, d);
    if (fs.existsSync(src)) copyTree(src, path.join(destSkillDir, d));
  }
  // 2) … then individual support files …
  for (const f of SUPPORT_FILES) {
    const src = path.join(pluginDirPath, f);
    if (fs.existsSync(src)) {
      const dst = path.join(destSkillDir, f);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.copyFileSync(src, dst);
    }
  }
  // 3) … then the skill's own files on top (SKILL.md + any skill-local overrides).
  copyTree(skill.srcDir, destSkillDir);
}

function samePath(a, b) {
  try {
    return fs.realpathSync(a) === fs.realpathSync(b);
  } catch {
    return path.resolve(a) === path.resolve(b);
  }
}

/**
 * Build a structured plan WITHOUT touching the filesystem (drives the summary,
 * the dry-run, and execution). `skills` carry srcDir + pluginDir for assembly.
 */
export function buildPlan({ scope, method, skills, agents, ctx }) {
  const store = storeDir(scope, ctx);
  const planSkills = skills.map((s) => ({
    name: s.name,
    srcDir: s.srcDir,
    pluginDir: s.pluginDir,
    storeDir: path.join(store, s.name),
  }));

  const planAgents = agents.map((agent) => {
    const dir = agentSkillsDir(agent, scope, ctx);
    const perSkill = planSkills.map((s) => {
      const target = path.join(dir, s.name);
      const isStore = samePath(dir, store);
      const action = isStore ? "store" : method; // 'store' | 'symlink' | 'copy'
      let overwrite = false;
      try {
        overwrite = !isStore && fs.lstatSync(target) && true;
      } catch {
        overwrite = false;
      }
      return { skill: s.name, target, action, overwrite };
    });
    return { id: agent.id, label: agent.label, dir, perSkill };
  });

  return { scope, method, store, skills: planSkills, agents: planAgents };
}

/** Replace whatever is at `target` (file, dir, or symlink). */
function removeIfPresent(target) {
  try {
    const st = fs.lstatSync(target);
    if (st.isDirectory() && !st.isSymbolicLink()) {
      fs.rmSync(target, { recursive: true, force: true });
    } else {
      fs.unlinkSync(target);
    }
    return true;
  } catch {
    return false;
  }
}

/** Execute a plan: assemble store bundles, then link/copy into each agent. */
export function execute(plan) {
  // 1) assemble each skill once into the universal store.
  for (const s of plan.skills) {
    fs.rmSync(s.storeDir, { recursive: true, force: true });
    assembleBundle(s.pluginDir, s, s.storeDir);
  }
  // 2) place each skill into every agent dir that isn't the store itself.
  const results = [];
  for (const agent of plan.agents) {
    for (const item of agent.perSkill) {
      const store = plan.skills.find((s) => s.name === item.skill).storeDir;
      if (item.action === "store") {
        results.push({ ...item, agent: agent.label, ok: true });
        continue;
      }
      fs.mkdirSync(agent.dir, { recursive: true });
      const replaced = removeIfPresent(item.target);
      try {
        if (item.action === "copy") {
          copyTree(store, item.target);
        } else {
          fs.symlinkSync(store, item.target, "dir");
        }
        results.push({ ...item, agent: agent.label, ok: true, replaced });
      } catch (err) {
        results.push({ ...item, agent: agent.label, ok: false, error: String(err) });
      }
    }
  }
  return results;
}

/** Lines describing the install, grouped per skill (mirrors the skills.sh summary). */
export function summaryLines(plan, home = os.homedir()) {
  const lines = [];
  for (const s of plan.skills) {
    lines.push(displayPath(s.storeDir, home));
    const direct = [];
    const linked = [];
    const overwrites = [];
    for (const a of plan.agents) {
      const item = a.perSkill.find((i) => i.skill === s.name);
      if (!item) continue;
      if (item.action === "store") direct.push(a.label);
      else linked.push(a.label);
      if (item.overwrite) overwrites.push(a.label);
    }
    if (direct.length) lines.push(`  universal (via ~/.agents/skills): ${direct.join(", ")}`);
    if (linked.length) lines.push(`  ${plan.method} → ${linked.join(", ")}`);
    if (overwrites.length) lines.push(`  overwrites: ${overwrites.join(", ")}`);
  }
  return lines;
}
