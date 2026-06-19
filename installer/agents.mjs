// Agent → skills-directory registry.
//
// Curated subset of the install targets supported by the `vercel-labs/skills`
// CLI (its `src/agents.ts` is the upstream source of truth; expand this list as
// needed). The install model is "universal store + symlink":
//
//   • The canonical skill payload is written ONCE to the universal store:
//       global  → ~/.agents/skills/<skill>
//       project → <cwd>/.agents/skills/<skill>
//   • Each selected agent gets the skill at its own skills dir. For agents whose
//     dir already IS the universal store (Codex, OpenCode, Gemini CLI, Copilot,
//     Amp, Warp, Zed, Cline) nothing extra is needed — the store IS their dir.
//   • Agents with a bespoke dir (Claude Code, Cursor, Hermes, OpenClaw, …) get a
//     symlink (or copy) from <agentDir>/<skill> → the store.
//
// Each agent declares `project(env, home)` (relative path, resolved against cwd)
// and `global(env, home)` (absolute path). Keeping these as functions avoids a
// custom ${VAR:-default} mini-language and stays trivially testable.

import path from "node:path";

const j = (...p) => path.join(...p);

export const AGENTS = [
  {
    id: "claude-code",
    label: "Claude Code",
    default: true,
    project: () => ".claude/skills",
    global: (env, home) => j(env.CLAUDE_CONFIG_DIR || j(home, ".claude"), "skills"),
  },
  {
    id: "openclaw",
    label: "OpenClaw",
    project: () => "skills",
    global: (env, home) => j(env.OPENCLAW_HOME || j(home, ".openclaw"), "skills"),
  },
  {
    id: "hermes",
    label: "Hermes",
    project: () => ".hermes/skills",
    global: (env, home) => j(env.HERMES_HOME || j(home, ".hermes"), "skills"),
  },
  {
    id: "cursor",
    label: "Cursor",
    project: () => ".agents/skills",
    global: (env, home) => j(home, ".cursor", "skills"),
  },
  {
    id: "windsurf",
    label: "Windsurf",
    project: () => ".windsurf/skills",
    global: (env, home) => j(home, ".codeium", "windsurf", "skills"),
  },
  {
    id: "aider-desk",
    label: "AiderDesk",
    project: () => ".aider-desk/skills",
    global: (env, home) => j(home, ".aider-desk", "skills"),
  },
  {
    id: "continue",
    label: "Continue",
    project: () => ".continue/skills",
    global: (env, home) => j(home, ".continue", "skills"),
  },
  {
    id: "goose",
    label: "Goose",
    project: () => ".goose/skills",
    global: (env, home) => j(env.XDG_CONFIG_HOME || j(home, ".config"), "goose", "skills"),
  },
  {
    id: "devin",
    label: "Devin",
    project: () => ".devin/skills",
    global: (env, home) => j(env.XDG_CONFIG_HOME || j(home, ".config"), "devin", "skills"),
  },
  // Universal agents: their global skills dir IS the universal store, so a single
  // write to ~/.agents/skills covers them all (no per-agent symlink needed).
  { id: "codex", label: "Codex", universal: true },
  { id: "opencode", label: "OpenCode", universal: true },
  { id: "gemini-cli", label: "Gemini CLI", universal: true },
  { id: "github-copilot", label: "GitHub Copilot", universal: true },
  { id: "cline", label: "Cline", universal: true },
  { id: "amp", label: "Amp", universal: true },
  { id: "warp", label: "Warp", universal: true },
  { id: "zed", label: "Zed", universal: true },
].map((a) =>
  a.universal
    ? { ...a, project: () => ".agents/skills", global: (e, h) => j(h, ".agents", "skills") }
    : a
);

/** The universal store dir for a scope (the single source of truth for payloads). */
export function storeDir(scope, { home, cwd }) {
  return scope === "global" ? path.join(home, ".agents", "skills") : path.join(cwd, ".agents", "skills");
}

/** Absolute skills dir for one agent at the given scope. */
export function agentSkillsDir(agent, scope, ctx) {
  const { env, home, cwd } = ctx;
  return scope === "global"
    ? agent.global(env, home)
    : path.resolve(cwd, agent.project(env, home));
}

export function getAgent(id) {
  return AGENTS.find((a) => a.id === id);
}
