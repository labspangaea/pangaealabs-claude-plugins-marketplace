# What can be shared between profiles, and what cannot

Two profiles = two config directories. The question for every entry is whether it describes *how
Claude Code behaves* (shareable) or *who you are and what you did* (never shareable).

## §1 Shareable — symlink from the second profile into the first

| Entry | Holds | Notes |
|---|---|---|
| `settings.json` | permissions, hooks, model, effort, status line, `enabledPlugins`, `extraKnownMarketplaces`, `env`, theme | The big one. Claude Code writes **through** the symlink, so either profile's change lands in the shared file. |
| `CLAUDE.md` | user-level memory | Link its `@file.md` imports too — they resolve next to the file. |
| `agents/` | custom subagent definitions | |
| `commands/` | custom slash commands | |
| `skills/` | personal skills (`claude plugin init` scaffolds here) | |
| `plugins/` | installed plugins, marketplace clones, catalog cache | Must be shared **as a whole directory** — see §3. |

`link_shared_config.py` covers exactly this list.

## §2 Never shareable

| Entry | Why |
|---|---|
| `.claude.json` | One file carrying the account identity, org, `projects` (per-directory trust and history), **and** `mcpServers`. Sharing it would merge the two accounts. |
| `.credentials.json` (Linux/WSL) | The OAuth token itself. |
| macOS keychain entry | Already per-profile: the service name is `Claude Code-credentials` plus a hash derived from the config dir. Nothing to do. |
| `sessions/`, `projects/`, `history.jsonl`, `shell-snapshots/`, `session-env/`, `file-history/` | Conversation state. Keeping it separate is the point of two profiles. Note what `projects/` actually holds: `projects/<encoded-cwd>/<session-id>.jsonl` is the **transcript** — the conversation itself, including whatever source code was read into it. `CLAUDE_CONFIG_DIR` moves that with everything else, so where you put a config directory decides where a client's code ends up on disk. |
| `statusline-spend/` and similar local ledgers | Per-subscription accounting; sharing it merges the two accounts' spend. |

## §3 The two traps

**MCP servers are stuck in the unshareable file.** `mcpServers` is a key of `.claude.json`, and it
is *not* a valid key of `settings.json` — putting it there is silently ignored (`claude mcp list`
reports nothing). So the server list has to be copied: that is what `sync_mcp.py` does, and why the
shell wrapper re-runs it on every launch.

`--mcp-config <file>` is a real alternative — it merges with the profile's own servers unless you
add `--strict-mcp-config` — but the flag is variadic, so `claude --mcp-config f "prompt"` eats the
prompt as a second config path. Only reach for it with another flag directly after it.

**The marketplace registry is split across two files.** `extraKnownMarketplaces` lives in
`settings.json` (shared), but `plugins/known_marketplaces.json` is per-profile. A marketplace
present only in the latter can never reach the second profile through shared settings, and every
plugin from it goes missing with no error — just a shorter `claude plugin list`. Sharing the whole
`plugins/` directory is what closes the gap.

The cost of sharing `plugins/`: two simultaneous sessions installing plugins write the same
directory. Install one at a time.

## §4 Things that are shared but should not be trusted blindly

Sharing `settings.json` also shares whatever it *points at* — hook commands, `statusLine.command`,
`apiKeyHelper`. Those scripts run in both profiles, so any absolute `~/.claude/...` path or
hardcoded account inside them is now wrong in one of the two. The usual symptom is a status line
showing the first profile's email in the second profile's session: the session is authenticated
correctly and only the display lies.

The fix pattern for any such script:

```sh
if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
    CFG_JSON="$CLAUDE_CONFIG_DIR/.claude.json"
else
    CFG_JSON="$HOME/.claude.json"      # NOT ~/.claude/.claude.json
fi
```

## §5 What the split does NOT cover

`CLAUDE_CONFIG_DIR` selects the *user-level* configuration directory. It has no effect on
per-project configuration: a repository's `.claude/settings.json`, `.claude/` skills and its
`CLAUDE.md` are found relative to the working directory and load under whichever profile is
running.

The practical consequence is a failure that looks like success. Run bare `claude` inside a client
repo and you get that repo's instructions, its permissions, its hooks — everything looks right —
while the session authenticates as your personal account and writes into your personal history. No
error, no warning. Two habits prevent it: never `export CLAUDE_CONFIG_DIR` in a shell rc (use a
named function per profile), and render the profile name in the status line so the wrong one is
visible rather than inferred.

## §6 Verifying two profiles are genuinely distinct

Compare `oauthAccount.accountUuid` and `organizationUuid`, not the email — a display string proves
nothing about which subscription is being billed. `profiles_doctor.py` flags two profiles signed in
as the same account, which is the failure that looks fine and quietly halves nothing: both sessions
draw on one subscription's rate limits.
