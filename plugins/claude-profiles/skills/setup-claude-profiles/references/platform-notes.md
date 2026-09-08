# Platform notes — macOS, Linux, WSL + Ubuntu

`profiles_doctor.py` reports the platform and the hazards below for the real machine. Read this when
you need the *why*, or when the doctor cannot run.

## §1 Where the OAuth token lives

| Platform | Store | Consequence |
|---|---|---|
| macOS | login keychain, service `Claude Code-credentials` plus a per-config-dir hash suffix (`Claude Code-credentials-3e915994`) | Profiles are isolated automatically. Nothing to configure, no file to protect. |
| Linux, WSL | `<config-dir>/.credentials.json` | Isolated because the config dirs differ, but it is a **plaintext file** — it must be mode `600`, and it must sit on a filesystem that can hold that mode. |

The doctor never queries the keychain (that can raise an access prompt); it uses the presence of
`oauthAccount` in `.claude.json` as the "is this profile signed in" signal.

A fresh config directory is **never** authenticated. Copying config in does not copy the login —
start the profile once interactively and run `/login`.

## §2 Which shell file to edit

| Platform | Default shell | File |
|---|---|---|
| macOS (Ventura+) | zsh | `~/.zshrc` |
| Ubuntu, WSL Ubuntu | bash | `~/.bashrc` |

The wrapper is a **function, not an alias**, because it has to run the MCP sync before launching:

```bash
claude-work() {
  local sync
  sync=$(sh -c 'ls -dt "$1"/.claude/plugins/cache/*/claude-profiles/*/skills/setup-claude-profiles/scripts/sync_mcp.py "$1"/.agents/skills/setup-claude-profiles/scripts/sync_mcp.py 2>/dev/null | head -1' _ "$HOME")
  [ -n "$sync" ] && [ -f "$sync" ] && python3 "$sync" --to "$HOME/.claude-work" --apply --quiet
  CLAUDE_CONFIG_DIR="$HOME/.claude-work" command claude "$@"
}
```

Resolve the script with a glob rather than a fixed path: the plugin cache carries a version
directory that changes on update, and `${CLAUDE_PLUGIN_ROOT}` means nothing inside a shell rc. The
guard makes a miss cost the MCP sync, never the launch.

Do not hand-edit that line — `shell_wrapper.py` writes it, and three details in it are load-bearing:

- **`sh -c`** wraps the globbing because **zsh sets `nomatch`**, so an unmatched glob is an *error
  raised while expanding the line*, before `ls` runs — which is why redirecting the command's
  stderr does not silence it. A fresh npx install with no plugin cache produced
  `claude-work:2: no matches found: …` and the function aborted. POSIX `sh` leaves an unmatched
  pattern literal, so `ls` merely fails and its stderr is discarded.
- **Two paths are searched.** `/plugin install` puts the scripts under
  `~/.claude/plugins/cache/<marketplace>/…`; the `npx` installer writes to the universal store at
  `~/.agents/skills/`. A machine that only ever ran `npx` has no plugin cache at all.
- **`-t`** sorts by modification time, newest first — the version installed most recently. A plain
  lexical sort picks the *oldest*, and reversing it is no better, since lexically `0.10.0` sorts
  below `0.9.0`.

Define the function *or* an alias of the same name, never both — in zsh an alias is expanded first
and shadows the function. Reload with `source ~/.bashrc` (or `~/.zshrc`), or open a new terminal.

## §3 WSL + Ubuntu

Everything here is the same as native Linux **except** where the files physically sit.

**Install Claude Code inside the distro, not on Windows.** If `command -v claude` answers with
something under `/mnt/c/...`, that is the Windows build reached through the filesystem bridge: it
resolves `HOME` and `CLAUDE_CONFIG_DIR` by Windows rules, and the two profiles will not behave as
described here. The doctor flags this.

**Keep both config directories on the Linux filesystem.** `~/.claude` and `~/.claude-work` on
ext4 — never `/mnt/c/Users/<you>/...`, and never a directory you reach through `\\wsl$` from
Windows and then symlink back. Windows drives appear in WSL2 as `9p` (and as `drvfs` in WSL1 and
for some mounts); on those:

- **symlinks are unreliable**, and the whole sharing scheme is symlinks;
- **Unix permission bits do not stick**, so `.credentials.json` cannot be held at `600` — your
  OAuth token ends up readable by anything that can read the drive;
- **the transcripts go there too.** `CLAUDE_CONFIG_DIR` relocates `projects/<encoded-cwd>/<session-id>.jsonl`,
  which is the conversation itself — including any source code read into it. On a Windows drive that
  lands in the Windows user profile, in reach of OneDrive/Known Folder Move, Search indexing and AV.
  For client work this is usually a bigger problem than the token, and it is the one people miss;
- I/O across the bridge is markedly slower, which you feel on every session start.

`link_shared_config.py` reads the mount table and refuses to run when the target is on one of those
filesystems — in dry run too, since reading `/proc/mounts` writes nothing. Under `--apply` it
additionally proves a symlink can really be created, by making and removing one, before it changes
anything; that probe is deliberately skipped in a dry run so a plan never writes to a directory you
may have named by mistake. Both checks are covered by `profiles_doctor.py --selfcheck`, which drives
them from a captured WSL `/proc/mounts` so the WSL logic is exercised even on a macOS box.

**Signing in.** `/login` opens a browser. Under WSL that may not launch anything; Claude Code prints
the URL, so copy it into a Windows browser and paste the code back. Installing `wslu` and setting
`BROWSER=wslview` makes it open by itself.

**Windows and WSL are separate installs.** A profile created under Windows and one created inside
the distro share nothing — not settings, not the keychain, not the credentials file. Pick one side
and put both profiles there.

## §4 Native Windows

Out of scope for this skill's scripts. `CLAUDE_CONFIG_DIR` itself works, but creating symlinks needs
Developer Mode or an elevated shell, so the sharing step will usually fail. The doctor says so
rather than pretending otherwise. Running both profiles inside WSL is the simpler path.

## §5 Quick platform checks

```bash
# Which platform does the tooling think this is?
python3 .../scripts/profiles_doctor.py --json | python3 -c "import json,sys; print(json.load(sys.stdin)['platform'])"

# WSL only: what filesystem is each profile on? (ext4 good, 9p/drvfs bad)
findmnt -no FSTYPE --target ~/.claude
findmnt -no FSTYPE --target ~/.claude-work

# Linux/WSL only: is the token file locked down?
stat -c '%a %n' ~/.claude-work/.credentials.json     # want 600
```
