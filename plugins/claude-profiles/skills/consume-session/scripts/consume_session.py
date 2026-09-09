#!/usr/bin/env python3
"""Read a session transcript published by publish-session into this profile.

Two ways to consume, because they cost wildly different amounts:

  digest  — flatten the transcript to the conversation only (human turns,
            Claude's prose, one line per tool call) and write it to a markdown
            file the reading session can page through. Drops thinking blocks and
            tool results, which is where ~90% of a transcript's bytes live.
  resume  — copy the raw transcript into this profile's projects/ directory so
            `claude --resume <id>` replays it exactly. Full fidelity, full
            context charge, and it needs a fresh session to take effect.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

DEFAULT_SHARED = Path.home() / "claude-profiles" / "shared-conversation"
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
HINT_KEYS = ("description", "file_path", "command", "pattern", "skill", "path", "prompt")


def shared_dir() -> Path:
    return Path(os.environ.get("CLAUDE_SHARED_SESSIONS_DIR", DEFAULT_SHARED)).expanduser()


def config_dir() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


def resolve(ref: str) -> Path:
    """Accept a bare session id, a filename, or a full path."""
    p = Path(ref).expanduser()
    if p.is_file():
        return p
    cand = shared_dir() / (ref if ref.endswith(".jsonl") else f"{ref}.jsonl")
    if cand.is_file():
        return cand
    sys.exit(f"No published transcript for {ref!r} (looked in {shared_dir()})")


def records(path: Path):
    for line in path.open(errors="ignore"):
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def clean(text: str) -> str:
    return REMINDER.sub("", text).strip()


def hint(tool_input) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for k in HINT_KEYS:
        v = tool_input.get(k)
        if isinstance(v, str) and v.strip():
            return " " + " ".join(v.split())[:100]
    return ""


def cmd_list(args) -> int:
    d = shared_dir()
    files = sorted(d.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True) if d.is_dir() else []
    if not files:
        print(f"Nothing published in {d}")
        return 0
    print(f"{d}:")
    for f in files:
        title = cwd = ""
        for rec in records(f):
            title = title or rec.get("aiTitle", "")
            cwd = cwd or rec.get("cwd", "")
            if title and cwd:
                break
        print(f"  {f.stem}  {f.stat().st_size / 1e6:6.1f} MB  {title or cwd}")
    return 0


def cmd_digest(args) -> int:
    src = resolve(args.session)
    meta, out, tools, skipped = {}, [], 0, 0
    for rec in records(src):
        if rec.get("isSidechain"):  # subagent chatter, not this conversation
            skipped += 1
            continue
        for k in ("cwd", "gitBranch", "aiTitle", "version"):
            if k in rec and k not in meta:
                meta[k] = rec[k]
        kind = rec.get("type")
        if kind not in ("user", "assistant"):
            continue
        content = rec.get("message", {}).get("content")
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
        who = "## User" if kind == "user" else "## Claude"
        for b in blocks:
            if not isinstance(b, dict):
                continue
            btype = b.get("type")
            if btype == "text":
                text = clean(b.get("text", ""))
                if text:
                    out.append(f"{who}\n\n{text[: args.max_block]}")
            elif btype == "tool_use":
                tools += 1
                out.append(f"`→ {b.get('name', '?')}{hint(b.get('input'))}`")
    if not out:
        sys.exit(f"{src} has no conversation content — is it a real transcript?")

    header = [f"# Shared session {src.stem}", ""]
    header += [f"- {k}: {v}" for k, v in meta.items()]
    header += [f"- source size: {src.stat().st_size / 1e6:.1f} MB", ""]
    body = "\n".join(header) + "\n" + "\n\n".join(out) + "\n"

    dest = Path(args.out).expanduser() if args.out else src.with_suffix(".digest.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body)
    print(f"digest:   {dest}")
    print(f"lines:    {body.count(chr(10)) + 1}")
    print(f"size:     {len(body) / 1000:.0f} KB (from {src.stat().st_size / 1e6:.1f} MB, "
          f"{tools} tool calls collapsed, {skipped} subagent records dropped)")
    return 0


def cmd_resume(args) -> int:
    src = resolve(args.session)
    cwd = next((r["cwd"] for r in records(src) if r.get("cwd")), None)
    if not cwd:
        sys.exit(f"{src} records no cwd, so its project directory can't be derived.")
    dest_dir = config_dir() / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists() and not args.force:
        sys.exit(f"{dest} already exists — pass --force to overwrite.")
    shutil.copy2(src, dest)
    sidecar = src.parent / src.stem
    if sidecar.is_dir():
        shutil.copytree(sidecar, dest_dir / src.stem, dirs_exist_ok=True)
    print(f"installed: {dest}" + (" (+ sidecar)" if sidecar.is_dir() else ""))
    print(f"profile:   {config_dir()}")
    print()
    print("Start a fresh session in that project and resume it:")
    print(f"  cd {cwd}")
    print(f"  claude --resume {src.stem}")
    return 0


def cmd_delete(args) -> int:
    src = resolve(args.session)
    if src.parent != shared_dir():
        sys.exit(f"Refusing to delete {src}: only files under {shared_dir()} are ours to remove.")
    src.unlink()
    for extra in src.parent.glob(f"{src.stem}.digest.md"):
        extra.unlink()
    sidecar = src.parent / src.stem
    had_sidecar = sidecar.is_dir()
    if had_sidecar:
        shutil.rmtree(sidecar)
    print(f"deleted: {src}" + (" (+ sidecar)" if had_sidecar else ""))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show published transcripts").set_defaults(fn=cmd_list)

    d = sub.add_parser("digest", help="flatten to a readable markdown file")
    d.add_argument("session", help="session id, filename, or path")
    d.add_argument("-o", "--out", default=None)
    d.add_argument("--max-block", type=int, default=4000, help="truncate each message to N chars")
    d.set_defaults(fn=cmd_digest)

    r = sub.add_parser("resume", help="install into this profile for `claude --resume`")
    r.add_argument("session")
    r.add_argument("--force", action="store_true")
    r.set_defaults(fn=cmd_resume)

    x = sub.add_parser("delete", help="remove a published transcript")
    x.add_argument("session")
    x.set_defaults(fn=cmd_delete)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
