#!/usr/bin/env python3
"""Share one profile's config with another by symlink. Dry-run by default.

    python3 link_shared_config.py --to ~/.claude-work            # show the plan
    python3 link_shared_config.py --to ~/.claude-work --apply    # do it
    python3 link_shared_config.py --to ~/.claude-work --unlink --apply

`--from` defaults to ~/.claude (the default profile). Anything the target
already owns is moved into <target>/backups/profile-link-<timestamp>/ before
the symlink replaces it, so `--unlink` can put it back. The undo COPIES out of
that backup rather than emptying it, so it can be run more than once, and it
writes a manifest of the links it removed.

A dry run writes nothing at all - not even the symlink-capability probe, which
only runs under --apply.

Claude Code writes THROUGH these symlinks rather than replacing them, so a
change made from either profile (enabling a plugin, adding a marketplace,
switching theme) lands in the single shared file and applies to both. That is
the point, and also the cost: there is no per-profile override once an entry
is shared.

What is deliberately NOT linked
-------------------------------
`.claude.json` holds the account identity, project history and the MCP server
list in one file, so it can never be shared — use sync_mcp.py for the MCP part.
Sessions, history and projects stay separate by design.
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _profiles import (  # noqa: E402
    DEFAULT_CONFIG_DIR,
    SHAREABLE,
    config_dir,
    host_platform,
    imported_memory_files,
    is_windows_filesystem,
    symlinks_work_in,
)


def plan_entries(src, requested):
    """Entries to link: those that exist in the source, plus CLAUDE.md imports."""
    names = list(requested or SHAREABLE)
    if "CLAUDE.md" in names and (src / "CLAUDE.md").is_file():
        for extra in imported_memory_files(src / "CLAUDE.md"):
            if extra not in names:
                names.append(extra)
    return [n for n in names if (src / n).exists() or (src / n).is_symlink()]


def classify(src_path, dst_path):
    """What has to happen to dst_path: 'ok', 'relink', 'replace' or 'create'."""
    if dst_path.is_symlink():
        current = os.path.realpath(str(dst_path))
        if current == os.path.realpath(str(src_path)):
            return "ok"
        return "relink"
    if dst_path.exists():
        return "replace"
    return "create"


def do_link(src_path, dst_path, backup_dir, apply_changes, log):
    action = classify(src_path, dst_path)
    if action == "ok":
        log("  = %-14s already shared" % dst_path.name)
        return False

    if action in ("relink", "replace"):
        if action == "replace":
            log("  ~ %-14s move aside -> %s/" % (dst_path.name, backup_dir.name))
            if apply_changes:
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst_path), str(backup_dir / dst_path.name))
        else:
            log("  ~ %-14s repoint symlink" % dst_path.name)
            if apply_changes:
                dst_path.unlink()

    log("  + %-14s -> %s" % (dst_path.name, src_path))
    if apply_changes:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.symlink_to(src_path, target_is_directory=src_path.is_dir())
    return True


def do_unlink(dst_path, backup_root, apply_changes, log):
    if not dst_path.is_symlink():
        log("  = %-14s not a shared link, left alone" % dst_path.name)
        return False
    log("  - %-14s remove link" % dst_path.name)
    if apply_changes:
        dst_path.unlink()
    restored = None
    if backup_root.is_dir():
        for candidate in sorted(backup_root.glob("profile-link-*"), reverse=True):
            if (candidate / dst_path.name).exists():
                restored = candidate / dst_path.name
                break
    if restored:
        log("  < %-14s restore from %s" % (dst_path.name, restored.parent.name))
        if apply_changes:
            # COPY, never move. Moving empties the backup, so a second --unlink
            # (after a re-link, or simply run twice) would have nothing left to
            # restore. The safety net has to survive being used.
            if restored.is_dir():
                shutil.copytree(str(restored), str(dst_path))
            else:
                shutil.copy2(str(restored), str(dst_path))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default=str(DEFAULT_CONFIG_DIR),
                    help="source profile whose config is shared (default: ~/.claude)")
    ap.add_argument("--to", dest="dst", required=True, help="target profile that borrows the config")
    ap.add_argument("--entries", nargs="*", default=None,
                    help="override the entry list (default: %s)" % " ".join(SHAREABLE))
    ap.add_argument("--unlink", action="store_true", help="undo: remove links and restore backups")
    ap.add_argument("--apply", action="store_true", help="make the changes (default is a dry run)")
    args = ap.parse_args(argv)

    src = config_dir(args.src)
    dst = config_dir(args.dst)

    if src == dst:
        print("--from and --to are the same directory (%s)." % src, file=sys.stderr)
        return 2
    if not src.is_dir():
        print("Source profile %s does not exist." % src, file=sys.stderr)
        return 2

    if not dst.is_dir():
        if not args.apply:
            print("Target %s does not exist yet; it will be created." % dst)
        else:
            dst.mkdir(parents=True, exist_ok=True)

    if not args.unlink and dst.is_dir():
        # Reading the mount table is free; do it in dry run too.
        if is_windows_filesystem(dst):
            print(
                "Refusing: %s is on a Windows filesystem. Under WSL, keep both profiles on "
                "the Linux filesystem (~/...), never under /mnt/c." % dst,
                file=sys.stderr,
            )
            return 3
        # The symlink probe CREATES a file, so it must not run during a dry run -
        # someone inspecting a plan should never have anything written on their
        # behalf, least of all in a directory they may have named by accident.
        if args.apply:
            ok, detail = symlinks_work_in(dst)
            if not ok:
                print("Refusing: %s cannot hold a symlink (%s)." % (dst, detail), file=sys.stderr)
                return 3

    backup_root = dst / "backups"
    backup_dir = backup_root / ("profile-link-%s" % time.strftime("%Y%m%d-%H%M%S"))
    lines = []
    log = lines.append

    log("platform: %s" % host_platform())
    log("%s  %s  %s" % (src, "<-- unlink" if args.unlink else "-->", dst))
    log("")

    names = plan_entries(src, args.entries) if not args.unlink else list(
        dict.fromkeys((args.entries or SHAREABLE) + imported_memory_files(src / "CLAUDE.md"))
    )
    if not names:
        log("Nothing to do: the source profile has none of the shareable entries.")

    changed = 0
    removed_links = []
    for name in names:
        if args.unlink:
            target = os.readlink(str(dst / name)) if (dst / name).is_symlink() else None
            if do_unlink(dst / name, backup_root, args.apply, log):
                changed += 1
                if target:
                    removed_links.append((name, target))
        else:
            changed += 1 if do_link(src / name, dst / name, backup_dir, args.apply, log) else 0

    log("")
    if args.apply:
        log("Applied. %d entr%s changed." % (changed, "y" if changed == 1 else "ies"))
        if args.unlink and removed_links:
            # A record of what was unlinked, so re-establishing the share later
            # does not depend on anyone remembering the entry list.
            manifest = backup_root / ("unlink-manifest-%s.txt" % time.strftime("%Y%m%d-%H%M%S"))
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                "# links removed from %s on %s\n%s\n"
                % (dst, time.strftime("%Y-%m-%d %H:%M:%S"),
                   "\n".join("%s -> %s" % (n, t) for n, t in removed_links)),
                encoding="utf-8",
            )
            log("Manifest of removed links: %s" % manifest)
            log("Backups are preserved, so --unlink can be run again safely.")
        if not args.unlink:
            log("MCP servers are not covered here — run sync_mcp.py --to %s" % dst)
    else:
        log("Dry run. %d entr%s would change. Re-run with --apply." % (changed, "y" if changed == 1 else "ies"))

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
