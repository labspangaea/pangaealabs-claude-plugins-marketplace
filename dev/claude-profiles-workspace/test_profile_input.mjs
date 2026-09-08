// Unit tests for the wizard's profile-name input handling.
//
//   node dev/claude-profiles-workspace/test_profile_input.mjs
//
// These exist because of a bug that reached a user's machine. The prompt's
// placeholder was written as a description — `work   →  ~/.claude-work` — and
// @clack/core inserts the placeholder VERBATIM as the value when Tab is pressed
// on an empty field:
//
//   u === "\t" && this.opts.placeholder && (this.value || this.rl.write(this.opts.placeholder))
//
// So a single Tab produced a profile directory literally named
// `.claude-work   →  ~/.claude-work`. Stripping whitespace could never have
// caught it, because the problem was not whitespace.
//
// The rule this file locks in: a placeholder is a VALUE, not a hint, and it must
// resolve to exactly what the same input typed by hand would.

import path from "node:path";

const REPO = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const { resolveProfileDir, profilePlaceholder, invalidProfileInput } =
  await import(path.join(REPO, "installer/profiles.mjs"));

const HOME = "/h";
let failed = 0;
const check = (label, ok, detail = "") => {
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${label}${ok ? "" : "   " + detail}`);
  if (!ok) failed++;
};

console.log("placeholder is a usable value (Tab-safe):");
for (const name of ["work", "client", "personal", "second", "profile5"]) {
  const ph = profilePlaceholder(name);
  const viaTab = String(resolveProfileDir(ph, HOME));
  const typed = String(resolveProfileDir(name, HOME));
  check(`Tab on "${name}" resolves like typing it`, viaTab === typed, `${viaTab} != ${typed}`);
  check(`placeholder "${ph}" is itself accepted`, !invalidProfileInput(ph), String(invalidProfileInput(ph)));
}

console.log("\nthe exact string that reached the user is rejected:");
const poisoned = "work   →  ~/.claude-work";
check("decorated placeholder is rejected", Boolean(invalidProfileInput(poisoned)), "accepted!");
check(
  "and would not have produced a directory",
  Boolean(invalidProfileInput(poisoned)),
  `resolveProfileDir gave ${resolveProfileDir(poisoned, HOME)}`
);

console.log("\nother malformed input is rejected:");
for (const bad of ["work -> x", "a b", "work\tx", "we ird", "→", "work→x"]) {
  check(`rejects ${JSON.stringify(bad)}`, Boolean(invalidProfileInput(bad)), "accepted!");
}

console.log("\nlegitimate input is still accepted:");
for (const good of ["work", "client-2", ".claude-work", "~/.claude-work", "/abs/path/.claude-x"]) {
  check(`accepts ${JSON.stringify(good)}`, !invalidProfileInput(good), String(invalidProfileInput(good)));
}

console.log("\nresolution is unchanged for good input:");
check("bare name", String(resolveProfileDir("work", HOME)) === "/h/.claude-work");
check("dot form", String(resolveProfileDir(".claude-work", HOME)) === "/h/.claude-work");
check("tilde form", String(resolveProfileDir("~/.claude-work", HOME)) === "/h/.claude-work");
check("absolute", String(resolveProfileDir("/abs/x", HOME)) === "/abs/x");

console.log(failed ? `\n${failed} FAILURES` : "\nall assertions passed");
process.exit(failed ? 1 : 0);
