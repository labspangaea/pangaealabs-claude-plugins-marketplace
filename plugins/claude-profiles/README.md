# claude-profiles — two Claude subscriptions, one machine, one config

Run a work account and a personal account (or a client's and your own) side by side on the same
laptop. Separate logins, separate rate limits, separate session history — but one set of settings,
plugins, skills, agents, commands, hooks and MCP servers, so you configure things once.

```bash
/plugin install claude-profiles@pangaealabs-claude-plugins-marketplace
```

Or through the marketplace's cross-agent installer, which adds a setup wizard — it reads which
profiles already exist, asks whether you run more than one subscription, collects the additional
profile names, shows the linker's dry run and asks once before sharing anything:

```bash
npx github:labspangaea/pangaealabs-claude-plugins-marketplace add claude-profiles
```

One skill, three scripts, no dependencies beyond Python 3.

## The idea

A **profile** is a config directory. `~/.claude` is the default; any other is chosen by exporting
`CLAUDE_CONFIG_DIR`. Everything Claude Code knows about you follows that variable, so two
directories give you two independent subscriptions.

Sharing is then a matter of deciding, per entry, whether it describes *how Claude Code behaves* or
*who you are*:

```
~/.claude-work/
  settings.json  ─┐
  CLAUDE.md       │
  agents/         ├─ symlinks into ~/.claude   (behaviour: shared)
  commands/       │
  skills/         │
  plugins/       ─┘
  .claude.json    ── account + history + MCP servers   (identity: never shared)
  sessions/  projects/  history.jsonl                  (identity: never shared)
```

MCP servers are the awkward case: they live under `mcpServers` in `.claude.json`, the same file that
carries the account — and `mcpServers` is not a valid key in `settings.json`. So they get copied,
not linked, and a shell wrapper re-copies them on every launch.

## The skill

`/setup-claude-profiles` walks the whole thing: create and sign in to the second profile, share the
config, mirror the MCP servers, wrap it in a shell function, verify. It also answers the questions
that come after — which account a session is really on, why a second profile has no plugins, how to
undo it.

### Scripts

| Script | What it does |
|---|---|
| `profiles_doctor.py` | **Read-only.** Every profile on the machine: config dir and its `.claude.json`, signed-in account and plan, credential store, which entries are shared and where they point, MCP server count, and the hazards — a config dir on a Windows filesystem, a filesystem that will not hold a symlink, a world-readable credentials file, two profiles on the same account. `--json` for machine output, `--selfcheck` to test the platform rules. |
| `link_shared_config.py` | Shares config between profiles by symlink. **Dry run by default and genuinely inert** — it writes nothing at all, not even the symlink-capability probe, which only runs under `--apply`. Anything the target owned is moved into `<target>/backups/profile-link-<ts>/` first. `--unlink --apply` reverses it, *copying* out of that backup rather than emptying it, so the undo can be run more than once, and recording a manifest of the links it removed. Idempotent. |
| `sync_mcp.py` | Mirrors `mcpServers` from one profile to another, preserving every other key and writing atomically. Idempotent, silent when already in sync, and both additions and removals propagate. |

## Platforms

macOS, Linux, and **WSL + Ubuntu**. The WSL differences are real rather than cosmetic: the OAuth
token is a plaintext `<config-dir>/.credentials.json` instead of a keychain entry, the shell file is
`~/.bashrc`, and both config directories have to stay on the Linux filesystem — on a Windows drive
seen through `/mnt` (`9p` or `drvfs`) symlinks are unreliable and the `600` mode on the token file
does not stick. `link_shared_config.py` reads the mount table and refuses to run there, and under
`--apply` it also proves a symlink can actually be created before it changes anything.

Native Windows is out of scope for the scripts: `CLAUDE_CONFIG_DIR` works, but symlink creation
needs Developer Mode or an elevated shell. Run both profiles inside WSL instead.

## Traps it knows about

- `~/.claude/.claude.json` often exists as a stale leftover and is **not** the default profile's
  live config — that is `~/.claude.json`. Reading the wrong one reports the wrong account.
- The marketplace registry is split between `settings.json` (`extraKnownMarketplaces`, shared) and
  `plugins/known_marketplaces.json` (per-profile). A marketplace present only in the second file
  never reaches the other profile, and its plugins go missing with no error.
- Anything shared that hardcodes a path or an account lies in the second profile. A status line with
  the email baked in is the classic: the session is on the right account, only the display is wrong.
- A shell opened inside a Claude Code session inherits `CLAUDE_CONFIG_DIR`, so a bare `claude` there
  targets that profile. Use `env -u CLAUDE_CONFIG_DIR claude …` for the default one.
- Two profiles signed in to the *same* account look completely healthy and share one subscription's
  rate limits. The doctor flags it; comparing `accountUuid` is the only real proof.
- **A half-shared profile looks tidy, not broken.** Share five entries and forget `skills/` and the
  second profile has *no* user-scoped skills at all — no error, nothing missing-looking, the skills
  just are not offered. The doctor now reports any entry the default profile has and a sharing
  profile lacks, because listing it as "absent" was not enough to make anyone notice.

---

© [Pangaea Digital Labs](https://www.pangaea.id/)
