#!/usr/bin/env node
// pangaealabs marketplace installer — the `npx` entry point.
//
//   npx github:labspangaea/pangaealabs-claude-plugins-marketplace
//   npx github:labspangaea/pangaealabs-claude-plugins-marketplace add docsmith -g
//
// Flow (mirrors the skills.sh TUI, plus docsmith's profile wizard):
//   plugins → skills → agents → scope → method → summary/confirm → install → profile.

import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

import * as p from "@clack/prompts";

import { AGENTS } from "./agents.mjs";
import { REPO_ROOT, readMarketplace, discoverSkills, pluginDir, shortHint } from "./marketplace.mjs";
import { buildPlan, execute, summaryLines, displayPath } from "./install.mjs";
import { runProfileWizard } from "./profile.mjs";

function parseArgs(argv) {
  const args = { plugins: [], agents: [], scope: null, method: null, dryRun: false, yes: false, noProfile: false, help: false };
  const rest = argv.slice(2);
  const pushList = (target, val) => {
    for (const v of String(val).split(",").map((s) => s.trim()).filter(Boolean)) target.push(v);
  };
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a === "add") {
      while (rest[i + 1] && !rest[i + 1].startsWith("-")) args.plugins.push(rest[++i]);
    } else if (a === "-a" || a === "--agent") pushList(args.agents, rest[++i] || "");
    else if (a.startsWith("--agent=")) pushList(args.agents, a.slice("--agent=".length));
    else if (a === "-g" || a === "--global") args.scope = "global";
    else if (a === "--project") args.scope = "project";
    else if (a === "--copy") args.method = "copy";
    else if (a === "--symlink") args.method = "symlink";
    else if (a === "--dry-run") args.dryRun = true;
    else if (a === "--no-profile") args.noProfile = true;
    else if (a === "-y" || a === "--yes") args.yes = true;
    else if (a === "-h" || a === "--help") args.help = true;
  }
  return args;
}

function bail(value) {
  if (p.isCancel(value)) {
    p.cancel("Cancelled.");
    process.exit(0);
  }
  return value;
}

const HELP = `pangaealabs marketplace installer

Usage:
  npx github:labspangaea/pangaealabs-claude-plugins-marketplace [add <plugin>...] [options]

Options:
  add <plugin>     Pre-select plugins (e.g. "add docsmith")
  -a, --agent <id> Pre-select agents (repeatable or comma-separated)
  -g, --global     Install for all projects (home dir)   [default: ask]
      --project    Install into the current project
      --copy       Copy skill files instead of symlinking
      --symlink    Symlink skill files (recommended)
      --no-profile Skip the docsmith profile.yaml wizard
      --dry-run    Show what would happen; write nothing
  -y, --yes        Skip the final confirmation
  -h, --help       Show this help

Agent ids: ${AGENTS.map((a) => a.id).join(", ")}
`;

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(HELP);
    return;
  }

  const ctx = { env: process.env, home: os.homedir(), cwd: process.cwd() };
  p.intro("pangaealabs — install marketplace skills into your agents");
  if (args.dryRun) p.log.warn("dry-run: nothing will be written.");

  // 1) plugins ----------------------------------------------------------------
  const market = readMarketplace(REPO_ROOT);
  const pluginChoices = market.plugins.map((pl) => ({
    value: pl.name,
    label: pl.name,
    hint: shortHint(pl.description, 70),
  }));
  let chosenPluginNames;
  if (args.plugins.length) {
    chosenPluginNames = args.plugins.filter((n) => market.plugins.some((pl) => pl.name === n));
    if (!chosenPluginNames.length) {
      p.cancel(`No matching plugins for: ${args.plugins.join(", ")}`);
      process.exit(1);
    }
    p.log.info(`Plugins: ${chosenPluginNames.join(", ")}`);
  } else if (pluginChoices.length === 1) {
    chosenPluginNames = [pluginChoices[0].value];
    p.log.info(`Plugin: ${chosenPluginNames[0]}`);
  } else {
    chosenPluginNames = bail(
      await p.multiselect({
        message: "Which plugins to install from the marketplace? (space to toggle)",
        options: pluginChoices,
        initialValues: [pluginChoices[0].value],
        required: true,
      })
    );
  }
  const chosenPlugins = market.plugins.filter((pl) => chosenPluginNames.includes(pl.name));

  // 2) skills -----------------------------------------------------------------
  const allSkills = [];
  for (const pl of chosenPlugins) {
    for (const sk of discoverSkills(REPO_ROOT, pl)) {
      allSkills.push({
        id: `${pl.name}/${sk.name}`,
        name: sk.name,
        description: sk.description,
        srcDir: sk.dir,
        pluginDir: pluginDir(REPO_ROOT, pl),
      });
    }
  }
  if (!allSkills.length) {
    p.cancel("No skills found in the selected plugins.");
    process.exit(1);
  }
  let chosenSkillIds;
  if (allSkills.length === 1) {
    chosenSkillIds = [allSkills[0].id];
    p.log.info(`Skill: ${allSkills[0].name}`);
  } else {
    chosenSkillIds = bail(
      await p.multiselect({
        message: "Select skills to install (space to toggle)",
        options: allSkills.map((s) => ({ value: s.id, label: s.name, hint: shortHint(s.description) })),
        initialValues: allSkills.map((s) => s.id),
        required: true,
      })
    );
  }
  const skills = allSkills.filter((s) => chosenSkillIds.includes(s.id));

  // 3) agents -----------------------------------------------------------------
  let chosenAgentIds;
  if (args.agents.length) {
    const known = new Set(AGENTS.map((a) => a.id));
    const unknown = args.agents.filter((id) => !known.has(id));
    if (unknown.length) {
      p.cancel(`Unknown agent(s): ${unknown.join(", ")}. Known: ${AGENTS.map((a) => a.id).join(", ")}`);
      process.exit(1);
    }
    chosenAgentIds = args.agents;
    p.log.info(`Agents: ${chosenAgentIds.join(", ")}`);
  } else {
    chosenAgentIds = bail(
      await p.multiselect({
        message: "Which agents do you want to install to? (space to toggle)",
        options: AGENTS.map((a) => ({
          value: a.id,
          label: a.label,
          hint: a.universal ? "via ~/.agents/skills" : undefined,
        })),
        initialValues: AGENTS.filter((a) => a.default).map((a) => a.id),
        required: true,
      })
    );
  }
  const agents = AGENTS.filter((a) => chosenAgentIds.includes(a.id));

  // 4) scope ------------------------------------------------------------------
  const scope =
    args.scope ||
    bail(
      await p.select({
        message: "Installation scope",
        options: [
          { value: "global", label: "Global", hint: "home dir — available across all projects" },
          { value: "project", label: "Project", hint: "current directory only" },
        ],
        initialValue: "global",
      })
    );

  // 5) method -----------------------------------------------------------------
  const method =
    args.method ||
    bail(
      await p.select({
        message: "Installation method",
        options: [
          { value: "symlink", label: "Symlink (recommended)", hint: "single source of truth, easy updates" },
          { value: "copy", label: "Copy", hint: "independent copies per agent" },
        ],
        initialValue: "symlink",
      })
    );

  // toolchain heads-up for docsmith (informational, never blocks the install) ---
  maybeToolchainNote(skills);

  // 6) summary + confirm ------------------------------------------------------
  const plan = buildPlan({ scope, method, skills, agents, ctx });
  p.note(summaryLines(plan, ctx.home).join("\n"), "Installation summary");
  p.note(
    `Source: ${displayPath(REPO_ROOT, ctx.home)} (first-party Pangaea Labs marketplace)\n` +
      `These are local repo skills — no third-party download, no Snyk/Socket/Gen scan is run.`,
    "Provenance"
  );

  if (!args.yes && !args.dryRun) {
    const go = bail(await p.confirm({ message: "Proceed with installation?", initialValue: true }));
    if (!go) {
      p.cancel("Aborted.");
      process.exit(0);
    }
  }

  // 7) install ----------------------------------------------------------------
  if (args.dryRun) {
    p.log.success("dry-run complete — no files written.");
  } else {
    const s = p.spinner();
    s.start("Installing skills…");
    const results = execute(plan);
    const failed = results.filter((r) => !r.ok);
    s.stop(failed.length ? "Installed with errors." : "Skills installed.");
    for (const f of failed) p.log.error(`${f.agent}: ${f.skill} — ${f.error}`);
  }

  // 8) docsmith profile wizard ------------------------------------------------
  const makePdf = skills.find((s) => s.name === "make-pdf");
  if (makePdf && args.noProfile) {
    p.log.info("profile setup skipped (--no-profile) — run setup_profile.py or make-pdf to configure it later.");
  } else if (makePdf) {
    const scriptPath = path.join(makePdf.pluginDir, "scripts", "setup_profile.py");
    const res = await runProfileWizard(p, { scriptPath, env: ctx.env, home: ctx.home, dryRun: args.dryRun });
    if (res.status === "written") p.log.success(`profile (${res.mode}) → ${displayPath(res.path, ctx.home)}`);
    else if (res.status === "dry-run") p.log.info(`dry-run: would write ${res.orgs.length} org(s) → ${displayPath(res.path, ctx.home)}`);
    else if (res.status === "skipped") p.log.info("profile setup skipped — make-pdf will offer it again on first use.");
    else if (res.status === "error") p.log.error(`profile setup failed: ${res.message}`);
  }

  p.outro(
    args.dryRun
      ? "Dry run finished."
      : "Done. Open a fresh agent session so it picks up the new skill(s)."
  );
}

function maybeToolchainNote(skills) {
  const docsmithSkill = skills.find((s) => s.name === "make-pdf");
  if (!docsmithSkill) return;
  const doctor = path.join(docsmithSkill.pluginDir, "scripts", "doctor.py");
  const r = spawnSync("python3", [doctor], { encoding: "utf8" });
  if (r.status && r.status !== 0) {
    p.log.warn(
      "docsmith renders PDFs locally and needs a toolchain (pandoc, tectonic, marp-cli, rsvg, " +
        "poppler, headless Chrome). doctor.py flags missing pieces:\n" +
        (r.stdout || r.stderr || "").trim()
    );
  }
}

main().catch((err) => {
  p.log.error(String(err?.stack || err));
  process.exit(1);
});
