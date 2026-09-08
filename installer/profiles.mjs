// claude-profiles setup wizard.
//
// Same division of labour as profile.mjs: the clack UI lives here, every decision
// that touches the filesystem is delegated to the plugin's own scripts
// (profiles_doctor.py, link_shared_config.py, sync_mcp.py). Those scripts are the
// canonical implementation the skill itself runs, so install-time setup and
// in-agent setup cannot drift apart — and the wizard inherits their safety
// properties for free: the linker is dry-run by default, refuses a Windows
// filesystem, and backs up anything it displaces.
//
// The wizard never invents a plan of its own. It shows the linker's real dry-run
// output, asks once, and only then re-runs the same command with --apply.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const SKILL_REL = path.join("skills", "setup-claude-profiles", "scripts");

export function scriptPaths(pluginDirPath) {
  const base = path.join(pluginDirPath, SKILL_REL);
  return {
    doctor: path.join(base, "profiles_doctor.py"),
    linker: path.join(base, "link_shared_config.py"),
    mcp: path.join(base, "sync_mcp.py"),
    wrapper: path.join(base, "shell_wrapper.py"),
    base,
  };
}

function py(script, argv, env) {
  return spawnSync("python3", [script, ...argv], {
    encoding: "utf8",
    // Merge over the parent env so PATH survives while HOME/CLAUDE_CONFIG_DIR
    // stay exactly what the wizard resolved its paths from. Getting this wrong
    // is how the docsmith wizard once wrote to a different dir than it reported.
    env: { ...process.env, ...env },
  });
}

/** Turn "work", ".claude-work", "~/x" or "/abs/x" into an absolute config dir. */
export function resolveProfileDir(input, home) {
  const s = String(input || "").trim();
  if (!s) return null;
  if (path.isAbsolute(s)) return s;
  if (s.startsWith("~/")) return path.join(home, s.slice(2));
  if (s.startsWith(".claude")) return path.join(home, s);
  // A bare word is a profile *name*: "work" -> ~/.claude-work
  return path.join(home, `.claude-${s.replace(/^\.?claude-?/, "")}`);
}

const short = (p_, home) => (p_.startsWith(home) ? p_.replace(home, "~") : p_);

/**
 * The placeholder for the profile-name prompt.
 *
 * It must be a VALID VALUE, never a description. @clack/core inserts the
 * placeholder verbatim when Tab is pressed on an empty field:
 *
 *   u === "\t" && this.opts.placeholder && (this.value || this.rl.write(this.opts.placeholder))
 *
 * A previous version read `work   →  ~/.claude-work`, so one Tab created a
 * directory literally named `.claude-work   →  ~/.claude-work` on a user's
 * machine. Explain the result in the prompt's message instead.
 */
export function profilePlaceholder(name) {
  return name;
}

/** Why this input cannot be a profile name, or undefined if it is fine. */
export function invalidProfileInput(value) {
  const s = String(value ?? "").trim();
  if (!s) return "Give a name (e.g. work) or a path.";
  // A path is allowed to contain slashes; a name is a single bare token. Neither
  // may contain whitespace or arrows — those only appear when descriptive text
  // has been captured as the value.
  if (/\s/.test(s)) return "No spaces or tabs — use a single name like `work`, or a path.";
  if (/[→←]|->|<-/.test(s)) return "That looks like hint text rather than a name. Type just the name, e.g. `work`.";
  if (/[\u0000-\u001f]/.test(s)) return "Contains a control character.";
  return undefined;
}

/**
 * Run the interactive wizard.
 *
 * Returns { status, ... } where status is one of:
 *   'written'  — at least one profile was linked (details in `results`)
 *   'planned'  — dry-run only, nothing written
 *   'skipped'  — user has one subscription, or declined
 *   'cancelled'| 'error' | 'unavailable'
 */
export async function runProfilesWizard(p, { pluginDir, env = process.env, home = os.homedir(), dryRun = false }) {
  const S = scriptPaths(pluginDir);
  if (!fs.existsSync(S.doctor)) return { status: "error", message: `not found: ${S.doctor}` };

  // Rewiring a config directory is not something to do to someone who cannot see
  // the prompts. Without a TTY, say so and leave the machine alone.
  if (!process.stdin.isTTY) {
    return { status: "unavailable", message: "no TTY — run the installer interactively to set up profiles" };
  }

  const probe = py(S.doctor, ["--json"], env);
  if (probe.status !== 0) {
    return { status: "error", message: (probe.stderr || probe.error?.message || "profiles_doctor.py failed").trim() };
  }
  let report;
  try {
    report = JSON.parse(probe.stdout);
  } catch (e) {
    return { status: "error", message: `could not parse profiles_doctor.py --json: ${e.message}` };
  }

  const profiles = report.profiles || [];
  const def = profiles.find((x) => x.is_default);
  const existing = profiles.filter((x) => !x.is_default);

  // "Check first if the user uses the default dir." Three things can be true and
  // each changes the advice, so report rather than assume.
  if (env.CLAUDE_CONFIG_DIR) {
    p.log.warn(
      `CLAUDE_CONFIG_DIR is set to ${short(env.CLAUDE_CONFIG_DIR, home)} in this shell, so "the default profile" ` +
        `is not what you are currently running. Unset it before sharing config, or the wizard will treat the ` +
        `wrong directory as your primary.`
    );
  }
  if (!def) {
    p.log.warn(`No default profile at ${short(path.join(home, ".claude"), home)} — nothing to share config FROM.`);
    return { status: "skipped", reason: "no-default-profile" };
  }
  if (!def.account?.logged_in) {
    p.log.warn(
      `The default profile at ${short(def.config_dir, home)} is not signed in. You can still link config, ` +
        `but verify with the doctor afterwards.`
    );
  }

  const who = def.account?.email ? `${def.account.email} [${def.account.plan}]` : "(not signed in)";
  p.note(
    [
      `Default profile : ${short(def.config_dir, home)} — ${who}`,
      `Live config     : ${short(def.config_json, home)}`,
      existing.length
        ? `Other profiles  : ${existing.map((x) => `${short(x.config_dir, home)} (${x.account?.email || "not signed in"})`).join(", ")}`
        : `Other profiles  : none found`,
      ``,
      `Sharing links settings.json, CLAUDE.md, agents/, commands/, skills/ and plugins/`,
      `from the default profile into each additional one. MCP servers are copied,`,
      `not linked — they live in the same file as the account.`,
    ].join("\n"),
    "claude-profiles — what is on this machine"
  );

  for (const problem of report.problems || []) p.log.warn(problem);

  const want = await p.confirm({
    message: "Do you have more than one Claude subscription to run on this machine?",
    initialValue: true,
  });
  if (p.isCancel(want)) return { status: "cancelled" };
  if (!want) {
    p.log.info(
      "Nothing to set up — the skill is installed and will walk you through it whenever you do add a second account."
    );
    return { status: "skipped", reason: "single-subscription" };
  }

  // Collect one or more ADDITIONAL profiles. The default profile always stays
  // where it is: relocating it costs a re-login and rewrites absolute paths.
  const targets = [];
  const suggestions = ["work", "client", "personal", "second"];
  for (;;) {
    const suggested = suggestions[targets.length] || `profile${targets.length + 2}`;
    const raw = await p.text({
      message:
        `Profile #${targets.length + 2} — name or directory ` +
        `(a name like "${suggested}" becomes ~/.claude-${suggested})`,
      // Value only: Tab inserts this verbatim.
      placeholder: profilePlaceholder(suggested),
      defaultValue: suggested,
      validate: (v) => {
        const bad = invalidProfileInput(v || suggested);
        if (bad) return bad;
        const dir = resolveProfileDir(v || suggested, home);
        if (!dir) return "Give a name (e.g. work) or a path.";
        if (dir === def.config_dir) return "That is the default profile — pick a different name.";
        if (targets.some((t) => t.dir === dir)) return "Already in the list.";
        return undefined;
      },
    });
    if (p.isCancel(raw)) return { status: "cancelled" };
    const dir = resolveProfileDir(raw || suggested, home);
    const known = profiles.find((x) => x.config_dir === dir);
    targets.push({ dir, existed: Boolean(known), account: known?.account?.email || null });

    const more = await p.confirm({ message: "Add another profile?", initialValue: false });
    if (p.isCancel(more)) return { status: "cancelled" };
    if (!more) break;
  }

  // Show the linker's OWN dry run for each target. This is the real plan, not a
  // description of one — and producing it writes nothing.
  const plans = [];
  for (const t of targets) {
    const r = py(S.linker, ["--from", def.config_dir, "--to", t.dir], env);
    plans.push({ ...t, ok: r.status === 0, out: (r.stdout || r.stderr || "").trim() });
  }
  for (const plan of plans) {
    p.note(plan.out || "(no output)", `Plan — ${short(plan.dir, home)}${plan.existed ? "" : "  (new)"}`);
  }
  const bad = plans.filter((x) => !x.ok);
  for (const b of bad) p.log.error(`${short(b.dir, home)}: the linker refused this target — see the plan above.`);
  const doable = plans.filter((x) => x.ok);
  if (!doable.length) return { status: "error", message: "no target could be linked" };

  if (dryRun) {
    p.log.info("dry-run: stopping before any change.");
    return { status: "planned", targets: doable.map((x) => x.dir) };
  }

  const go = await p.confirm({
    message: `Apply this sharing to ${doable.length} profile${doable.length === 1 ? "" : "s"}? (backups are kept; --unlink reverses it)`,
    initialValue: true,
  });
  if (p.isCancel(go)) return { status: "cancelled" };
  if (!go) return { status: "skipped", reason: "declined-apply" };

  const results = [];
  for (const t of doable) {
    const link = py(S.linker, ["--from", def.config_dir, "--to", t.dir, "--apply"], env);
    const mcp = py(S.mcp, ["--from", def.config_dir, "--to", t.dir, "--apply"], env);
    results.push({
      dir: t.dir,
      linked: link.status === 0,
      linkOut: (link.stdout || link.stderr || "").trim(),
      // sync_mcp exits non-zero until the profile has been started and signed in.
      // That is expected on a brand-new directory, not a failure of the setup.
      mcp: mcp.status === 0 ? "synced" : "pending-login",
      mcpOut: (mcp.stdout || mcp.stderr || "").trim(),
    });
  }

  const rcResult = await offerRcAppend(p, {
    script: S.wrapper,
    dirs: results.filter((r) => r.linked).map((r) => r.dir),
    env, home, dryRun,
  });

  return { status: "written", results, rcResult, defaultDir: def.config_dir };
}

// --- shell rc handling ------------------------------------------------------
// Delegated to the plugin's shell_wrapper.py, exactly as the docsmith wizard
// delegates to setup_profile.py. It has to live in the PLUGIN, not here: someone
// who installs with `/plugin install` never runs this installer, and if the rc
// logic lived only in the installer their launcher would silently never be
// registered. Same script, same behaviour, whichever way the plugin arrived.

async function offerRcAppend(p, { script, dirs, env, home, dryRun }) {
  if (!dirs.length) return { status: "skipped", reason: "no-profiles" };

  const argv = dirs.flatMap((d) => ["--to", d]);
  const probe = py(script, [...argv, "--json"], env);
  if (probe.status !== 0) {
    return { status: "error", message: (probe.stderr || "shell_wrapper.py failed").trim() };
  }
  let plan;
  try {
    plan = JSON.parse(probe.stdout);
  } catch (e) {
    return { status: "error", message: `could not parse shell_wrapper.py --json: ${e.message}` };
  }

  for (const c of plan.clashes) p.log.warn(c);
  p.note(
    `${short(plan.rc_file, home)}${plan.rc_exists ? "" : "   (will be created)"}\n\n${plan.block}`,
    plan.action === "update" ? "Update the existing claude-profiles block?" : "Add to your shell startup file?"
  );
  if (dryRun) return { status: "dry-run", ...plan };

  const go = await p.confirm({
    message: plan.action === "update"
      ? `Replace the existing claude-profiles block in ${short(plan.rc_file, home)}?`
      : `Append this to ${short(plan.rc_file, home)}? (a timestamped backup is written first)`,
    initialValue: true,
  });
  if (p.isCancel(go)) return { status: "cancelled", ...plan };
  if (!go) return { status: "declined", ...plan };

  const res = py(script, [...argv, "--apply", "--json"], env);
  if (res.status !== 0) {
    return { status: "error", message: (res.stderr || "shell_wrapper.py --apply failed").trim() };
  }
  try {
    return JSON.parse(res.stdout);
  } catch (e) {
    return { status: "error", message: `could not parse shell_wrapper.py --apply: ${e.message}` };
  }
}
