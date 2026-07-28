#!/usr/bin/env node
// pangaealabs marketplace installer — the `npx` entry point.
//
//   npx github:labspangaea/pangaealabs-claude-plugins-marketplace
//   npx github:labspangaea/pangaealabs-claude-plugins-marketplace add docsmith -g
//
// Flow (mirrors the skills.sh TUI, plus a per-plugin post-install step):
//   plugins → skills → agents → scope → method → summary/confirm → install → [docsmith profile].
// Multi-skill plugins (e.g. testcraft) prompt a skill multiselect; pre-select with -s/--skill
// to run non-interactively.

import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

import * as p from "@clack/prompts";

import { AGENTS } from "./agents.mjs";
import { REPO_ROOT, readMarketplace, discoverSkills, pluginDir, shortHint } from "./marketplace.mjs";
import { buildPlan, execute, summaryLines, displayPath } from "./install.mjs";
import { runProfileWizard } from "./profile.mjs";

function parseArgs(argv) {
  const args = { plugins: [], skills: [], agents: [], scope: null, method: null, dryRun: false, yes: false, noProfile: false, help: false };
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
    else if (a === "-s" || a === "--skill") pushList(args.skills, rest[++i] || "");
    else if (a.startsWith("--skill=")) pushList(args.skills, a.slice("--skill=".length));
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
  add <plugin>     Pre-select plugins (e.g. "add docsmith", "add go-scaffolder")
  -s, --skill <id> Pre-select skills by name (repeatable or comma-separated;
                   needed to install a multi-skill plugin like testcraft non-interactively)
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
  if (args.skills.length) {
    const want = new Set(args.skills);
    const matched = allSkills.filter((s) => want.has(s.id) || want.has(s.name));
    if (!matched.length) {
      p.cancel(`No matching skills for: ${args.skills.join(", ")}. Available: ${allSkills.map((s) => s.name).join(", ")}`);
      process.exit(1);
    }
    chosenSkillIds = matched.map((s) => s.id);
    p.log.info(`Skills: ${matched.map((s) => s.name).join(", ")}`);
  } else if (allSkills.length === 1) {
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

// Informational, per-plugin toolchain heads-ups — printed when a plugin that
// generates code against an external toolchain is being installed but the
// toolchain looks missing/too old. Never blocks the install.
function maybeToolchainNote(skills) {
  const inPlugin = (name) => skills.some((s) => path.basename(s.pluginDir) === name);

  // docsmith: local PDF toolchain, probed by its own doctor.py
  const docsmithSkill = skills.find((s) => s.name === "make-pdf");
  if (docsmithSkill) {
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

  // go-scaffolder: generates Go services against the public go-lib module
  if (inPlugin("go-scaffolder")) {
    const r = spawnSync("go", ["version"], { encoding: "utf8" });
    const v = (r.stdout || "").match(/go(\d+)\.(\d+)/);
    const ok = v && (Number(v[1]) > 1 || (Number(v[1]) === 1 && Number(v[2]) >= 26));
    if (!ok) {
      p.log.warn(
        `go-scaffolder generates Go services and needs Go 1.26+ on PATH ${v ? `(found go${v[1]}.${v[2]})` : "(go not found)"}.\n` +
          "It also expects the go-lsp MCP server (gopls) for post-write diagnostics. Generated " +
          "services fetch github.com/labspangaea/go-lib from the public Go proxy — no token, no GOPRIVATE."
      );
    }
  }

  // elysia-scaffolder: generates ElysiaJS/Bun services against the public @labspangaea/ts-lib
  if (inPlugin("elysia-scaffolder")) {
    const r = spawnSync("bun", ["--version"], { encoding: "utf8" });
    const v = (r.stdout || "").trim().match(/^(\d+)\.(\d+)/);
    const ok = v && (Number(v[1]) > 1 || (Number(v[1]) === 1 && Number(v[2]) >= 1));
    if (!ok) {
      p.log.warn(
        `elysia-scaffolder generates ElysiaJS/Bun services and needs Bun 1.1+ on PATH ${v ? `(found ${v[1]}.${v[2]})` : "(bun not found)"}.\n` +
          "It also expects the ts-lsp MCP server for diagnostics. Generated services install " +
          "@labspangaea/ts-lib from the public npm registry — no token, no .npmrc auth."
      );
    }
  }
}

main().catch((err) => {
  p.log.error(String(err?.stack || err));
  process.exit(1);
});
