#!/usr/bin/env python3
"""Mirror user-scope MCP servers from one profile to another. Idempotent.

    python3 sync_mcp.py --to ~/.claude-work            # show what would change
    python3 sync_mcp.py --to ~/.claude-work --apply
    python3 sync_mcp.py --to ~/.claude-work --apply --quiet   # for a shell wrapper

Why this exists instead of a symlink: user-scope MCP servers live under the
`mcpServers` key of `<config-dir>/.claude.json`, the same file that carries the
account identity, project trust and conversation history. That file cannot be
shared between profiles, and `mcpServers` is NOT a valid key in settings.json
(which can be shared), so the server list has to be copied.

Only the `mcpServers` key is touched; every other key in the target file is
preserved, and the write is atomic. Both additions and removals propagate, so
the target ends up matching the source exactly.

Servers that authenticate over OAuth still need a one-time `/mcp` login in the
target profile — tokens are per-profile and are not copied by this script.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _profiles import (  # noqa: E402
    DEFAULT_CONFIG_DIR,
    config_dir,
    config_json_for,
    read_json,
    write_json_atomic,
)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=str(DEFAULT_CONFIG_DIR),
                    help="profile to copy MCP servers from (default: ~/.claude)")
    ap.add_argument("--to", dest="dst", required=True, help="profile to copy them to")
    ap.add_argument("--apply", action="store_true", help="write the change (default is a dry run)")
    ap.add_argument("--quiet", action="store_true", help="print only when something changed")
    args = ap.parse_args(argv)

    src_dir, dst_dir = config_dir(args.src), config_dir(args.dst)
    if src_dir == dst_dir:
        print("--from and --to are the same profile (%s)." % src_dir, file=sys.stderr)
        return 2

    src_json, dst_json = config_json_for(src_dir), config_json_for(dst_dir)
    if not src_json.exists():
        print("Source %s not found — has that profile ever been started?" % src_json, file=sys.stderr)
        return 2
    if not dst_json.exists():
        print("Target %s not found — start that profile once and sign in first." % dst_json, file=sys.stderr)
        return 2

    servers = read_json(src_json).get("mcpServers") or {}
    target = read_json(dst_json)
    if not target:
        print("Target %s is empty or unreadable; refusing to overwrite it." % dst_json, file=sys.stderr)
        return 2

    before = target.get("mcpServers") or {}
    if before == servers:
        if not args.quiet:
            print("already in sync (%d MCP server%s)" % (len(servers), "" if len(servers) == 1 else "s"))
        return 0

    added = sorted(set(servers) - set(before))
    removed = sorted(set(before) - set(servers))
    changed = sorted(n for n in set(servers) & set(before) if servers[n] != before[n])
    summary = "; ".join(filter(None, [
        ("+" + ", +".join(added)) if added else "",
        ("-" + ", -".join(removed)) if removed else "",
        ("~" + ", ~".join(changed)) if changed else "",
    ])) or "config differs"

    if not args.apply:
        print("would sync %s -> %s: %s (dry run; pass --apply)" % (src_json, dst_json, summary))
        return 0

    target["mcpServers"] = servers
    write_json_atomic(dst_json, target)
    print("synced MCP servers to %s: %s" % (dst_dir, summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
