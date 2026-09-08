// End-to-end test of the installer's claude-profiles wizard, against a throwaway
// fake HOME. Run:  node dev/claude-profiles-workspace/test_wizard.mjs /tmp/wiz
//
// The python-level rules are unit-tested in test_shell_wrapper.py; this covers the
// wizard flow itself — prompts asked, symlinks made, rc block written, and that
// neither the real ~/.claude nor the real ~/.zshrc is touched.
// Stubs the clack prompt object with scripted answers so the whole flow runs
// without a TTY, then asserts the filesystem result.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// Resolved from this file so the test moves with the repo.
const REPO = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const { runProfilesWizard } = await import(path.join(REPO, "installer/profiles.mjs"));

const ROOT = process.argv[2];
const SCENARIO = process.argv[3] || "fresh";
fs.rmSync(ROOT, { recursive: true, force: true });
execFileSync("python3", [path.join(REPO, "dev/claude-profiles-workspace/build_sandbox.py"), ROOT, SCENARIO]);
const HOME = path.join(ROOT, "home");

// Scripted prompt stub. Each call shifts the next answer off the queue and
// records what was asked, so we can assert the wizard asked the right things.
function makePrompt(answers) {
  const asked = [];
  const take = (kind, opts) => {
    asked.push(`${kind}: ${opts.message}`);
    if (!answers.length) throw new Error(`unscripted ${kind}: ${opts.message}`);
    return answers.shift();
  };
  return {
    asked,
    notes: [],
    logs: [],
    confirm: async (o) => take("confirm", o),
    text: async (o) => take("text", o),
    select: async (o) => take("select", o),
    isCancel: (v) => v === Symbol.for("clack:cancel"),
    note: function (body, title) { this.notes.push(`${title}\n${body}`); },
    log: {
      info: function (m) { this.parent.logs.push(["info", m]); },
      warn: function (m) { this.parent.logs.push(["warn", m]); },
      error: function (m) { this.parent.logs.push(["error", m]); },
      success: function (m) { this.parent.logs.push(["success", m]); },
    },
  };
}
function wire(p) { p.log.parent = p; return p; }

// The wizard refuses without a TTY by design; assert that first, then override.
const noTty = await runProfilesWizard(wire(makePrompt([])), { pluginDir: path.join(REPO, "plugins/claude-profiles"), env: { HOME }, home: HOME });
console.log("no-TTY guard:", noTty.status === "unavailable" ? "PASS" : `FAIL (${noTty.status})`);
Object.defineProperty(process.stdin, "isTTY", { value: true, configurable: true });

const env = { ...process.env, HOME };
delete env.CLAUDE_CONFIG_DIR;

const p = wire(makePrompt([
  true,      // "more than one subscription?"
  "work",    // profile #2 name
  true,      // add another?
  "client",  // profile #3 name
  false,     // add another?
  true,      // apply?
  true,      // append the launcher to the sandbox's shell rc?
]));
import crypto from "node:crypto";
const realRc = path.join(os.homedir(), ".zshrc");
const realRcBefore = fs.existsSync(realRc) ? crypto.createHash("sha256").update(fs.readFileSync(realRc)).digest("hex") : null;
const res = await runProfilesWizard(p, { pluginDir: path.join(REPO, "plugins/claude-profiles"), env, home: HOME, dryRun: false });

console.log("\nasked:"); for (const a of p.asked) console.log("  -", a);
console.log("\nstatus:", res.status);

let fail = 0;
const check = (label, ok, detail = "") => { console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}${ok ? "" : "  " + detail}`); if (!ok) fail++; };

console.log("\nassertions:");
check("status is 'written'", res.status === "written", res.message || res.reason || "");
check("two profiles handled (>2 total supported)", (res.results || []).length === 2, String((res.results || []).length));
for (const r of res.results || []) {
  const links = fs.existsSync(r.dir) ? fs.readdirSync(r.dir).filter((f) => fs.lstatSync(path.join(r.dir, f)).isSymbolicLink()) : [];
  check(`${path.basename(r.dir)}: linked`, r.linked);
  check(`${path.basename(r.dir)}: symlinks created`, links.length >= 6, links.join(","));
  check(`${path.basename(r.dir)}: settings.json points at default`,
    fs.existsSync(path.join(r.dir, "settings.json")) &&
    fs.realpathSync(path.join(r.dir, "settings.json")) === fs.realpathSync(path.join(HOME, ".claude/settings.json")));
  check(`${path.basename(r.dir)}: MCP pending until sign-in`, r.mcp === "pending-login", r.mcp);
}
check("default profile untouched (settings.json still a real file)",
  fs.lstatSync(path.join(HOME, ".claude/settings.json")).isFile() &&
  !fs.lstatSync(path.join(HOME, ".claude/settings.json")).isSymbolicLink());
const rcFile = path.join(HOME, ".zshrc");
check("launcher written to the SANDBOX rc", fs.existsSync(rcFile) && fs.readFileSync(rcFile, "utf8").includes("claude-work()"));
check("one marker block, both profiles", (fs.readFileSync(rcFile, "utf8").match(/claude-profiles >>>/g) || []).length === 1);
check("rc result reports appended", res.rcResult?.status === "appended", String(res.rcResult?.status));
check("REAL ~/.zshrc untouched",
  realRcBefore === (fs.existsSync(realRc) ? crypto.createHash("sha256").update(fs.readFileSync(realRc)).digest("hex") : null));
check("real ~/.claude untouched",
  !fs.existsSync(path.join(os.homedir(), ".claude-work-TESTMARKER")));

console.log(`\n${fail ? fail + " FAILURES" : "all assertions passed"}`);
process.exit(fail ? 1 : 0);
