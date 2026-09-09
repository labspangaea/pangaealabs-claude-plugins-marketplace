---
name: publish-session
description: >
  Hand the CURRENT conversation off to another Claude Code profile / subscription by copying this
  session's transcript into a shared staging directory (~/claude-profiles/shared-conversation/) that
  every profile on the machine can read. Use this whenever the user wants to continue, resume, move,
  hand over, or share what you are working on right now with their other account — phrasings like
  "share this session with my work profile", "I want to keep going on this under claude-work",
  "hand this conversation over to my personal subscription", "export this session so my other login
  can pick it up", "publish this conversation", "I'm running out of limits, move this to the other
  account", or "continue this in claude-personal". Also trigger when the user hits a rate limit or
  plan cap mid-task and asks how to carry the context to their other subscription. Each profile sets
  its own CLAUDE_CONFIG_DIR and therefore has a completely separate session list, so a session
  recorded under one profile is invisible to `claude --resume` under another — this skill is the
  bridge. Do NOT use to load a session someone already published (that is `consume-session`), or to
  set up the profiles themselves (that is `setup-claude-profiles`).
---

# Publish this session to the shared hand-off directory

A Claude Code profile is just a `CLAUDE_CONFIG_DIR`. Transcripts live under
`$CLAUDE_CONFIG_DIR/projects/<slugified-cwd>/<session-id>.jsonl`, so a session recorded by the
default `~/.claude` profile simply does not exist as far as a `~/.claude-work` profile is concerned.
Publishing copies the transcript somewhere both can see.

`PLUGIN_DIR` below is this skill's own directory — the `publish-session/` folder holding this file,
whether that is inside the installed plugin or a standalone `~/.agents/skills/publish-session`.

## Step 1 — stamp a nonce into the transcript

Run this **on its own**, in its own Bash call, with a fresh random string each time:

```bash
echo "ptl-<8 random hex chars>"
```

## Step 2 — publish, in a LATER Bash call

```bash
python3 PLUGIN_DIR/scripts/publish_session.py --nonce ptl-<the same string>
```

The two calls have to be separate. The transcript is flushed only once a tool call returns, so a
nonce echoed in the same command the script runs in will not be on disk yet and the script will
exit 1 telling you so — if that happens, just echo a new nonce and try again.

**Why a nonce at all:** the obvious "newest `.jsonl` in this project directory" heuristic picks the
wrong file whenever the user has two sessions open in the same project, which is exactly the
situation someone juggling two subscriptions is in. Grepping for a string only this conversation
contains is unambiguous.

## Step 3 — tell the user how to pick it up

The script prints the session id and the published path. Relay both, plus the command for the
other profile:

```
/claude-profiles:consume-session <session-id>
```

## Things worth saying out loud

- **The copy is a snapshot.** The live transcript keeps growing as this conversation continues, so
  anything said after publishing is not in the copy. If the user wants the last few turns included,
  publish again at the end — re-running just overwrites the same file.
- **The transcript is the whole conversation**, including file contents and command output that
  scrolled past. If this session touched credentials or client data, say so before publishing —
  the staging directory is plain files in the user's home, readable by anything running as them.
- **Nothing is deleted or moved.** The original session stays exactly where it is and remains
  resumable under this profile.
