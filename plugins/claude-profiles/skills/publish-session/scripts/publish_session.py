#!/usr/bin/env python3
"""Copy the CURRENT session's transcript into the shared hand-off directory.

Finding "the current session" is the only hard part. Two sessions can be running
in the same project directory at the same time, so newest-mtime picks the wrong
file often enough to matter. Instead the caller echoes a nonce into the
transcript first, and we grep for it: exactly one transcript can contain it.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

DEFAULT_SHARED = Path.home() / "claude-profiles" / "shared-conversation"


def shared_dir() -> Path:
    return Path(os.environ.get("CLAUDE_SHARED_SESSIONS_DIR", DEFAULT_SHARED)).expanduser()


def config_dirs() -> list[Path]:
    """Profiles to search, current one first.

    CLAUDE_CONFIG_DIR is inherited by shells inside a session, so it names the
    profile we are running under. The glob is the fallback for the default
    profile, which sets nothing.
    """
    seen, out = set(), []
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    for cand in ([Path(env).expanduser()] if env else []) + [Path.home() / ".claude"] + sorted(
        Path.home().glob(".claude-*")
    ):
        p = cand / "projects"
        if p.is_dir() and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def find_by_nonce(nonce: str) -> Path | None:
    hits = []
    for projects in config_dirs():
        for f in projects.rglob("*.jsonl"):
            try:
                if nonce in f.read_text(errors="ignore"):
                    hits.append(f)
            except OSError:
                continue
    # ponytail: a nonce collides with itself only if the caller reuses one;
    # newest wins so a reused nonce still resolves to this session.
    return max(hits, key=lambda f: f.stat().st_mtime) if hits else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nonce", required=True, help="unique string already echoed into this transcript")
    ap.add_argument("--out-dir", default=None, help="override the shared directory")
    args = ap.parse_args(argv)

    src = find_by_nonce(args.nonce)
    if src is None:
        print(
            f"No transcript contains {args.nonce!r}.\n"
            "Echo the nonce in its own Bash call first, then run this in a LATER call — "
            "the transcript is only flushed once the previous call returns.",
            file=sys.stderr,
        )
        return 1

    dest_dir = Path(args.out_dir).expanduser() if args.out_dir else shared_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)

    # A session is the .jsonl PLUS a sidecar directory of the same name holding
    # subagent transcripts and tool results too large to inline. Copying only the
    # .jsonl loses those silently, and `claude --resume` then replays a session
    # whose subagent runs and big outputs are simply gone.
    sidecar = src.parent / src.stem
    extra = 0
    if sidecar.is_dir():
        dest_sidecar = dest_dir / src.stem
        shutil.copytree(sidecar, dest_sidecar, dirs_exist_ok=True)
        extra = sum(f.stat().st_size for f in dest_sidecar.rglob("*") if f.is_file())

    size_mb = (dest.stat().st_size + extra) / 1e6
    print(f"session_id: {src.stem}")
    print(f"published:  {dest}")
    print(f"size:       {size_mb:.1f} MB" + (f" (incl. {extra / 1e6:.1f} MB sidecar)" if extra else ""))
    print(f"source:     {src}")
    print()
    print("In the other profile, run:  /claude-profiles:consume-session " + src.stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
