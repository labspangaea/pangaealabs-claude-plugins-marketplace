---
name: consume-session
description: >
  Pick up a conversation that another Claude Code profile / subscription published into the shared
  staging directory (~/claude-profiles/shared-conversation/), so this session inherits what the
  other one already worked out. Use whenever the user wants to load, import, absorb, continue, or
  resume a session that came from their other account — phrasings like "load the session I shared
  from my work profile", "pick up where claude-personal left off", "consume <session-id>", "import
  the shared conversation", "what did my other account already do on this", "read the handoff
  transcript", or just pasting a bare session UUID and asking you to carry on with it. Also trigger
  when the user says they published a session from another profile and now wants it here, or asks
  what shared sessions are waiting to be picked up. Offers two paths: a cheap markdown digest read
  into this session, or installing the raw transcript so `claude --resume <id>` replays it in full.
  Always ends by asking whether to delete or keep the staged file. Do NOT use to publish the
  current conversation (that is `publish-session`) or to configure profiles (`setup-claude-profiles`).
---

# Consume a session published by another profile

`PLUGIN_DIR` below is this skill's own directory — the `consume-session/` folder holding this file,
whether that is inside the installed plugin or a standalone `~/.agents/skills/consume-session`.

## Step 1 — find out what is waiting

```bash
python3 PLUGIN_DIR/scripts/consume_session.py list
```

Each row is a session id, its size, and its title or working directory. If the user already gave
you an id, skip straight to step 2. If the list is empty, the other profile has not published yet —
tell them to run `/claude-profiles:publish-session` over there first.

## Step 2 — pick digest or resume

These cost very different amounts, so choose deliberately rather than defaulting to whichever is
mentioned first.

**Digest (the normal choice).** Flattens the transcript to the conversation itself — human turns,
Claude's prose, one line per tool call — and drops thinking blocks, tool results and subagent
chatter, which is where the overwhelming majority of a transcript's bytes live. A 2 MB transcript
typically lands around 20 KB. It works immediately, in this session, with no restart.

```bash
python3 PLUGIN_DIR/scripts/consume_session.py digest <session-id>
```

Then read the file it names. If it is very long, read the tail first — the end of a session is
where the conclusions are — and page backwards only if you need the reasoning behind them.

**Resume (full fidelity).** Copies the raw transcript into this profile's `projects/` directory so
Claude Code can replay it exactly.

```bash
python3 PLUGIN_DIR/scripts/consume_session.py resume <session-id>
```

This does **not** affect the running session — it prints a `cd` and a `claude --resume <id>` to run
in a fresh terminal. Say that plainly, because "resume" sounds like it should take effect here.
Worth flagging too: replaying the whole transcript re-reads every token of it, which on the profile
the user switched to precisely because of rate limits is a real cost before their first question.
Reach for it when they need the exact file-edit history back, not just the knowledge.

## Step 3 — summarise what you inherited

Do not just announce that the digest was read. Tell the user, in a few lines, what the other
session established: what it was trying to do, what it settled on, and what it left unfinished.
That summary is the actual deliverable — it is what lets them ask their next question without
re-explaining anything.

## Step 4 — ask about the staged file

Use `AskUserQuestion` to ask whether to delete or keep the staged transcript. Ask once, after the
content has been used, so the answer is informed rather than a guess.

If the user already answered this in their own request — "clean up after yourself", "delete it once
you're done", "keep it, I'll consume it from my third profile too" — act on what they said instead
of asking again. Re-asking a question the user has already answered reads as not having listened.
Say which way you went, so a misread is easy to correct.

- **Delete** — the hand-off is done. It is a full copy of a conversation sitting in the user's home
  directory, so removing it once consumed is the tidy default.
- **Keep** — they may consume it again from a third profile, or want it as a record.

Deleting removes the staged copy and its digest, and nothing else:

```bash
python3 PLUGIN_DIR/scripts/consume_session.py delete <session-id>
```

The original transcript in the publishing profile is untouched either way — the script refuses to
delete anything outside the shared directory.
