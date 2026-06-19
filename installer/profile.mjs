// docsmith profile wizard.
//
// Collects one-or-more org entries in the installer's own clack UI, then hands the
// answers to the CANONICAL writer (plugins/docsmith/scripts/setup_profile.py
// --json) so the YAML shape lives in exactly one place — the same script that
// make-pdf's Step 0 runs on first use. That keeps install-time setup and in-agent
// setup byte-identical, and means non-Claude agents (no AskUserQuestion) get a
// working profile too.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const CONFIDENTIALITY = ["", "Public", "Internal", "Confidential", "Restricted"];

const FIELDS = [
  { key: "company", message: "Company / organization name", required: true, placeholder: "Acme Corp" },
  { key: "author", message: "Author / docs contact", placeholder: "Jane Rivera" },
  { key: "email", message: "Contact email", placeholder: "press@acme.example" },
  { key: "logo", message: "Logo path (square SVG/PNG; blank = none)", placeholder: "~/.docsmith/logo/acme.png" },
  { key: "wordmark", message: "Wordmark (text fallback when no logo)", placeholder: "ACME" },
  { key: "website", message: "Website URL", placeholder: "https://acme.example" },
  { key: "copyright", message: "Copyright notice", placeholder: "© 2026 Acme Corp" },
];

export function profilePath(env = process.env, home = os.homedir()) {
  const base = env.DOCSMITH_HOME || path.join(home, ".docsmith");
  return path.join(base, "profile.yaml");
}

/**
 * Run the interactive wizard. Returns:
 *   { status: 'written'|'skipped'|'cancelled'|'error'|'dry-run', mode, orgs, path, message }
 */
export async function runProfileWizard(p, { scriptPath, env = process.env, home = os.homedir(), dryRun = false }) {
  const dest = profilePath(env, home);
  const exists = fs.existsSync(dest);

  p.note(
    `make-pdf brands every document as one of your orgs.\nThis writes ${dest.replace(home, "~")}.`,
    "Set up docsmith profile.yaml"
  );

  const want = await p.confirm({
    message: exists ? "Update your brand profile now?" : "Set up your brand profile now?",
    initialValue: true,
  });
  if (p.isCancel(want)) return { status: "cancelled" };
  if (!want) return { status: "skipped", path: dest };

  const orgs = [];
  for (;;) {
    const org = {};
    let cancelled = false;
    for (const f of FIELDS) {
      const val = await p.text({
        message: `Org #${orgs.length + 1} — ${f.message}`,
        placeholder: f.placeholder,
        validate: f.required ? (v) => (v && v.trim() ? undefined : "Required") : undefined,
      });
      if (p.isCancel(val)) {
        cancelled = true;
        break;
      }
      org[f.key] = (val || "").trim();
    }
    if (cancelled) return { status: "cancelled" };

    const conf = await p.select({
      message: `Org #${orgs.length + 1} — default confidentiality`,
      options: CONFIDENTIALITY.map((c) => ({ value: c, label: c || "(none)" })),
      initialValue: "",
    });
    if (p.isCancel(conf)) return { status: "cancelled" };
    org.default_confidentiality = conf;

    orgs.push(org);

    const more = await p.confirm({ message: "Add another organization?", initialValue: false });
    if (p.isCancel(more)) return { status: "cancelled" };
    if (!more) break;
  }

  let mode = "overwrite";
  if (exists) {
    const choice = await p.select({
      message: "A profile already exists — how should we apply these?",
      options: [
        { value: "append", label: "Append", hint: "keep existing orgs, add these" },
        { value: "overwrite", label: "Overwrite", hint: "replace the whole file" },
        { value: "skip", label: "Skip", hint: "leave it as-is" },
      ],
      initialValue: "append",
    });
    if (p.isCancel(choice)) return { status: "cancelled" };
    mode = choice;
  }
  if (mode === "skip") return { status: "skipped", path: dest, orgs };

  if (dryRun) {
    return { status: "dry-run", mode, orgs, path: dest };
  }

  // Spawn the canonical writer with the SAME env we resolved paths from, so
  // setup_profile.py honours the identical $DOCSMITH_HOME (merged over the parent
  // env so PATH etc. survive). Without this, the writer would fall back to the
  // process default and write somewhere other than where the wizard reported.
  const res = spawnSync("python3", [scriptPath, "--json", "--mode", mode], {
    input: JSON.stringify(orgs),
    encoding: "utf8",
    env: { ...process.env, ...env },
  });
  if (res.status !== 0) {
    return {
      status: "error",
      mode,
      orgs,
      path: dest,
      message: (res.stderr || res.error?.message || "setup_profile.py failed").trim(),
    };
  }
  return { status: "written", mode, orgs, path: (res.stdout || dest).trim() };
}
