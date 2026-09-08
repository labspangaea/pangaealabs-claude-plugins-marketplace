---
name: setup-claude-profiles
description: >
  Run two or more Claude Code subscriptions side by side on one machine — a work account and a
  personal one, or a client account and your own — each with its own login, rate limits and session
  history, while they share one set of settings, plugins, skills, agents, commands, hooks and MCP
  servers. Use whenever someone says they have two Claude accounts or two Claude Max/Pro
  subscriptions and wants both on the same laptop, wants to keep work and personal Claude Code
  separate, wants a second config directory, mentions `CLAUDE_CONFIG_DIR`, asks why a second profile
  has none of their plugins or MCP servers, asks why `claude-work` still shows the wrong account or
  email, wants to copy or share settings from `~/.claude` into another config dir, or asks how to
  stop burning one subscription's quota when they have two. Also use for the reverse questions —
  "which account is this session actually using", "did my second profile pick up my MCP servers",
  "is my token stored per profile", "how do I undo the sharing" — and for the same setup under WSL /
  Ubuntu, where the config directory must stay off the Windows drive or the symlinks and file
  permissions silently break. Ships three python3 scripts: a read-only doctor that reports every
  profile on the machine with its account, plan, credential store and hazards; an idempotent
  dry-run-first linker that shares config between profiles and can undo itself; and an MCP mirror,
  because MCP servers live in the one file that can never be shared. Do NOT use to switch models,
  to log in to a single account, to configure hooks or permissions inside one profile
  (`update-config` owns that), or to move a plugin between marketplaces.
---

# setup-claude-profiles

Two subscriptions, one machine, one set of config.

## The model

A **profile** is a config directory. `~/.claude` is the default one; any other is selected by
exporting `CLAUDE_CONFIG_DIR` before launching. Everything Claude Code stores about *you* follows
that variable — settings, plugins, skills, sessions, history, the account — so two directories give
you two independent logins with independent rate limits.

Two facts decide the whole design, and both are easy to get wrong:

| | Default profile | `CLAUDE_CONFIG_DIR=<dir>` |
|---|---|---|
| account + MCP servers | `~/.claude.json` | `<dir>/.claude.json` |
| everything else | `~/.claude/…` | `<dir>/…` |

`~/.claude/.claude.json` often exists too, as a stale leftover. **It is not the default profile's
live config** — reading it reports the wrong account. `_profiles.config_json_for()` encodes the rule;
use it rather than joining paths by hand.

And `mcpServers` is a key of `.claude.json`, **not** of `settings.json`. Since `.claude.json` also
carries the account identity and project history, it can never be shared — so MCP servers are the
one thing that must be *copied* rather than linked.

## Workflow

Run the doctor first, always. It is read-only and tells you what actually exists rather than what
the user believes exists.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup-claude-profiles/scripts/profiles_doctor.py
```

**1 — Create and sign in to the second profile.** A fresh config dir is not authenticated; the
token does not carry over from the first profile.

```bash
CLAUDE_CONFIG_DIR=~/.claude-work claude    # then /login, with the SECOND account
```

Pick the directory per `references/platform-notes.md` — on WSL this is the step where people put it
on `/mnt/c` and quietly break everything downstream.

**2 — Share the config.** Dry run first; it prints the plan and changes nothing.

```bash
python3 .../scripts/link_shared_config.py --to ~/.claude-work
python3 .../scripts/link_shared_config.py --to ~/.claude-work --apply
```

It symlinks `settings.json`, `CLAUDE.md`, `agents/`, `commands/`, `plugins/` and `skills/` from
`~/.claude`, moves anything the target already owned into `<target>/backups/profile-link-<ts>/`, and
also links whatever `CLAUDE.md` pulls in with `@file.md` — an `@`-import resolves next to the file,
so linking `CLAUDE.md` alone leaves it dangling. `--unlink --apply` reverses all of it, copying out
of that backup rather than emptying it, so the undo survives being run more than once and leaves a
manifest of the links it removed. The dry run writes nothing whatsoever — worth saying to anyone
nervous about pointing it at the wrong directory.

**3 — Mirror the MCP servers.**

```bash
python3 .../scripts/sync_mcp.py --to ~/.claude-work --apply
```

**4 — Register a launcher**, so the mirror runs on every launch and the server list can never
drift. `shell_wrapper.py` writes it, and is dry-run by default like the linker:

```bash
python3 .../scripts/shell_wrapper.py --to ~/.claude-work            # show the plan
python3 .../scripts/shell_wrapper.py --to ~/.claude-work --apply
```

It picks `~/.zshrc` or `~/.bashrc` from `$SHELL`, backs the file up first, and writes between
`# >>> claude-profiles >>>` markers so re-running replaces its own block rather than stacking
duplicates. Pass `--to` more than once to register several profiles in one block.

Read what it prints before applying, because two things it reports are easy to wave past. An
**alias** of the same name already existing means the function will never run — in zsh an alias is
expanded before a same-named function is considered, so appending underneath one looks like it
worked and changes nothing. An existing **function** of the same name means two definitions, and
the later one wins; that is ours, but it is confusing to read six months later.

The launcher is a function rather than an alias because an alias cannot run the sync first. It
resolves the sync script by glob, since the plugin cache carries a version directory that changes
on update and `${CLAUDE_PLUGIN_ROOT}` means nothing inside a shell rc; the guard makes a miss cost
the MCP sync, never the launch.

Do not reach for `--mcp-config` here instead: the flag works and merges with the profile's own
servers, but it is variadic, so `claude --mcp-config f "prompt"` swallows the prompt as a second
config path.

**5 — Verify.** Re-run the doctor. Then confirm the accounts really differ — compare
`accountUuid`, not just the email:

```bash
python3 .../scripts/profiles_doctor.py --json | python3 -c \
  "import json,sys; [print(p['config_dir'], p['account']['email'], p['account']['account_uuid']) for p in json.load(sys.stdin)['profiles']]"
```

## What to tell the user afterwards

- **Shared means shared both ways.** Claude Code writes *through* the symlinks, so enabling a plugin
  or changing the theme from either profile changes the single shared file and applies to both.
  There is no per-profile override once an entry is shared — that is the trade, and it is worth
  saying out loud before they discover it.
- **OAuth-based MCP servers still need one `/mcp` login per profile.** The server *definition*
  copies; its token does not. Expect `⚠ N MCP servers need authentication` on first launch.
- **Anything that hardcodes a path or an account will lie in the second profile.** A shared status
  line with the email baked in is the classic case: the session is on the right account and only the
  display is wrong. Derive such values from `CLAUDE_CONFIG_DIR` (falling back to `~/.claude.json`),
  and check any shared script for absolute `~/.claude/...` paths.
- **A shell inside a Claude Code session inherits `CLAUDE_CONFIG_DIR`.** So a bare `claude ...` in a
  terminal opened by the second profile targets *that* profile. Use `env -u CLAUDE_CONFIG_DIR claude
  ...` to act on the default one, and never compare two profiles without setting the directory
  explicitly on both sides.
- **`CLAUDE_CONFIG_DIR` separates *user-level* config only — not per-project config.** A repo's
  `.claude/settings.json` and `CLAUDE.md` load whichever profile you launch. So typing bare `claude`
  in a client's repo out of habit looks completely normal — right project instructions, right
  behaviour — while running on the wrong subscription and writing to the wrong history. This is the
  most common way the split quietly fails, which is why the wrapper is a named function and
  `CLAUDE_CONFIG_DIR` is never exported globally.
- **Put the profile name in the status line, not just the email.** If the wrapper is bypassed or
  `CLAUDE_CONFIG_DIR` is lost, Claude Code falls back to the default profile silently — the one case
  that genuinely does bill the wrong account. A label derived from `CLAUDE_CONFIG_DIR` at render
  time is the only thing on screen that would reveal it.

## Say what your evidence actually is

Most of this is checkable on the spot, and where it is, check it rather than recalling it. But some
of it cannot be: a session running on macOS cannot observe a WSL mount table, and a session with no
second profile yet cannot observe how that profile behaves.

When you report something you did not observe on this machine, name the basis in the same sentence
as the claim — "the documented behaviour of drvfs mounts", "the captured mount table
`profiles_doctor.py --selfcheck` runs against", "what the linker would refuse" — rather than phrasing
it as a measurement. "I checked your path against a WSL mount table" is false when the table was a
fixture, and the reader has no way to catch it. This matters more here than in most tasks: the whole
point of the doctor is that people should stop guessing at their own config, and an answer that
blurs a fixture into a measurement teaches exactly the habit the skill exists to replace.

Being explicit costs a clause and loses nothing — a reader who knows which parts were measured knows
which parts to re-check on their own machine.

## References

- `references/what-is-shared.md` — the full shareable / never-shareable matrix and why each falls
  where it does, including the marketplace registry being split across two files.
- `references/platform-notes.md` — macOS, Linux and **WSL + Ubuntu**: where the credential store
  is, which shell file to edit, and the `/mnt/c` trap.

`profiles_doctor.py --selfcheck` asserts the platform rules — including the WSL filesystem
detection, driven from a captured `/proc/mounts` so it runs on macOS too.
