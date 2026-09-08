#!/usr/bin/env python3
"""Register a per-profile launcher function in the user's shell startup file.

    shell_wrapper.py --to ~/.claude-work                 # show the plan, write nothing
    shell_wrapper.py --to ~/.claude-work --apply
    shell_wrapper.py --to ~/.claude-work --to ~/.claude-client --apply
    shell_wrapper.py --to ~/.claude-work --json          # machine-readable, for the installer
    shell_wrapper.py --selfcheck

This is the canonical writer, called from two places so they cannot drift: the
`npx` installer's wizard, and step 4 of the skill itself. Someone who installs
the plugin with `/plugin install` never runs the installer, so putting this logic
only in the installer would mean the launcher silently never gets registered on
their machine.

Appending to a shell rc is a different class of act from writing inside a config
directory this tool owns: the file is hand-curated, ordering matters, and a bad
edit breaks every future shell. So:

  * nothing is written without --apply;
  * the original is copied to <rc>.bak-claude-profiles-<timestamp> first;
  * the block sits between markers, so re-running replaces its own block instead
    of stacking duplicates, and deleting it is one clean cut;
  * an existing alias or function of the same name is reported rather than
    quietly fought. In zsh an alias is expanded before a same-named function is
    considered, so appending a function underneath one looks like it worked and
    changes nothing.
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _profiles import config_dir, unusable_profile_dir  # noqa: E402

BEGIN = "# >>> claude-profiles >>>"
END = "# <<< claude-profiles <<<"
NOTE = "# Added by claude-profiles. Safe to delete this whole block."


def rc_path(env=None, home=None):
    """The startup file for the user's login shell: zsh -> .zshrc, else .bashrc."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    return home / (".zshrc" if "zsh" in env.get("SHELL", "") else ".bashrc")


def function_name(profile_dir):
    """~/.claude-work -> claude-work; ~/.claude-client -> claude-client."""
    base = Path(profile_dir).name
    stem = re.sub(r"^\.claude-?", "", base)
    return "claude-%s" % (stem or "alt")


def function_text(profile_dir, home=None):
    """The launcher: mirror MCP servers, then start Claude on that profile.

    The sync script is resolved by glob rather than a fixed path because the
    plugin cache carries a version directory that changes on update, and
    ${CLAUDE_PLUGIN_ROOT} means nothing inside a shell rc. The guard makes a miss
    cost the MCP sync, never the ability to launch.
    """
    home = Path.home() if home is None else Path(home)
    d = str(profile_dir).replace(str(home), "$HOME")
    return "\n".join([
        "%s() {" % function_name(profile_dir),
        "  local sync",
        '  sync=$(ls -d "$HOME"/.claude/plugins/cache/*/claude-profiles/*/skills/setup-claude-profiles/scripts/sync_mcp.py 2>/dev/null | head -1)',
        '  [ -n "$sync" ] && python3 "$sync" --to "%s" --apply --quiet' % d,
        '  CLAUDE_CONFIG_DIR="%s" command claude "$@"' % d,
        "}",
    ])


def existing_definitions(text, name):
    """Does `text` already define `name` as an alias or a function?"""
    esc = re.escape(name)
    return {
        "alias": bool(re.search(r"^\s*alias\s+%s=" % esc, text, re.M)),
        "func": bool(re.search(r"^\s*(function\s+)?%s\s*\(\)" % esc, text, re.M)),
    }


def render_block(profile_dirs, home=None):
    body = [function_text(d, home) for d in profile_dirs]
    return "\n".join([BEGIN, NOTE] + body + [END])


def splice_block(text, block):
    """Replace an existing marker block, else append one."""
    start, end = text.find(BEGIN), text.find(END)
    if start != -1 and end != -1 and end > start:
        return text[:start] + block + text[end + len(END):]
    sep = "" if (not text or text.endswith("\n")) else "\n"
    return "%s%s\n%s\n" % (text, sep, block)


def strip_block(text):
    """The file with our block removed — used to look for OTHER definitions."""
    start, end = text.find(BEGIN), text.find(END)
    if start != -1 and end != -1 and end > start:
        return text[:start] + text[end + len(END):]
    return text


def plan(profile_dirs, rc_file, home=None):
    rc_file = Path(rc_file)
    exists = rc_file.exists()
    text = rc_file.read_text(encoding="utf-8") if exists else ""
    has_block = BEGIN in text
    outside = strip_block(text)
    clashes = []
    for d in profile_dirs:
        name = function_name(d)
        found = existing_definitions(outside, name)
        if found["alias"]:
            clashes.append(
                "%s: an alias of that name already exists. In zsh an alias is expanded before a "
                "same-named function, so the function would never run — remove the alias." % name
            )
        elif found["func"]:
            clashes.append(
                "%s: a function of that name is already defined outside our block. The later "
                "definition wins, which would be ours; two definitions are confusing to read later."
                % name
            )
    return {
        "rc_file": str(rc_file),
        "rc_exists": exists,
        "action": "update" if has_block else "append",
        "block": render_block(profile_dirs, home),
        "names": [function_name(d) for d in profile_dirs],
        "clashes": clashes,
    }


def apply(pl):
    rc_file = Path(pl["rc_file"])
    text = rc_file.read_text(encoding="utf-8") if rc_file.exists() else ""
    backup = None
    if rc_file.exists():
        backup = "%s.bak-claude-profiles-%s" % (rc_file, time.strftime("%Y%m%d%H%M%S"))
        shutil.copy2(rc_file, backup)
    rc_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(rc_file) + ".tmp-claude-profiles"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(splice_block(text, pl["block"]))
    os.replace(tmp, rc_file)
    return backup


def selfcheck():
    import tempfile
    failures, ran = [], []

    def check(label, got, want):
        ran.append(label)
        if got != want:
            failures.append("%s: got %r, want %r" % (label, got, want))

    check("name from .claude-work", function_name("/h/.claude-work"), "claude-work")
    check("name from .claude-client", function_name("/h/.claude-client"), "claude-client")
    check("name from a bare dir", function_name("/h/.claude"), "claude-alt")
    check("home is collapsed to $HOME", "$HOME/.claude-work" in function_text("/h/.claude-work", "/h"), True)

    check("alias detected", existing_definitions("alias claude-work='x'\n", "claude-work")["alias"], True)
    check("function detected", existing_definitions("claude-work() {\n}\n", "claude-work")["func"], True)
    check("function with keyword detected",
          existing_definitions("function claude-work() {\n}\n", "claude-work")["func"], True)
    check("unrelated name not matched", existing_definitions("claude-worker() {}\n", "claude-work")["func"], False)

    # Splicing is idempotent: applying twice leaves exactly one block.
    base = "export PATH=/usr/bin\n"
    b1 = render_block(["/h/.claude-work"], "/h")
    once = splice_block(base, b1)
    twice = splice_block(once, b1)
    check("append then re-apply leaves one block", twice.count(BEGIN), 1)
    check("re-apply is a no-op", once, twice)
    check("existing content preserved", twice.startswith(base), True)

    # A changed profile set REPLACES the block rather than stacking.
    b2 = render_block(["/h/.claude-work", "/h/.claude-client"], "/h")
    grown = splice_block(once, b2)
    check("block replaced, not duplicated", grown.count(BEGIN), 1)
    check("new profile present", "claude-client()" in grown, True)

    # Our own block must not be mistaken for a pre-existing definition.
    with tempfile.TemporaryDirectory() as tmp:
        rc = Path(tmp) / ".zshrc"
        rc.write_text(once, encoding="utf-8")
        pl = plan(["/h/.claude-work"], rc, "/h")
        check("our own block is not a clash", pl["clashes"], [])
        check("second run is an update", pl["action"], "update")

        rc.write_text("alias claude-work='claude'\n", encoding="utf-8")
        pl2 = plan(["/h/.claude-work"], rc, "/h")
        check("a real alias clash is reported", len(pl2["clashes"]), 1)
        check("alias clash names zsh shadowing", "alias" in pl2["clashes"][0], True)

    for line in failures:
        print("FAIL " + line)
    print("selfcheck: %d passed, %d failed" % (len(ran) - len(failures), len(failures)))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", dest="profiles", action="append", default=[],
                    help="a profile config dir to add a launcher for (repeatable)")
    ap.add_argument("--rc", help="shell startup file (default: ~/.zshrc or ~/.bashrc from $SHELL)")
    ap.add_argument("--apply", action="store_true", help="write the change (default is a dry run)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selfcheck", action="store_true", help="test the rules and exit")
    args = ap.parse_args(argv)

    if args.selfcheck:
        return selfcheck()
    if not args.profiles:
        ap.error("give at least one --to <profile dir>")

    dirs = []
    for d in args.profiles:
        resolved = config_dir(d)
        bad = unusable_profile_dir(resolved)
        if bad:
            print("Refusing %r: %s" % (str(resolved), bad), file=sys.stderr)
            return 2
        dirs.append(str(resolved))
    rc_file = Path(os.path.expanduser(args.rc)) if args.rc else rc_path()
    pl = plan(dirs, rc_file)

    if args.apply:
        pl["backup"] = apply(pl)
        pl["status"] = "appended" if pl["action"] == "append" else "updated"
    else:
        pl["status"] = "dry-run"

    if args.json:
        print(json.dumps(pl, indent=2))
        return 0

    print("%s  (%s)%s" % (pl["rc_file"], pl["action"], "" if pl["rc_exists"] else "  — will be created"))
    for c in pl["clashes"]:
        print("  ! " + c)
    print()
    print(pl["block"])
    print()
    if args.apply:
        print("Written.%s" % (" Backup: %s" % pl["backup"] if pl.get("backup") else ""))
        print("Reload with: source %s" % pl["rc_file"])
    else:
        print("Dry run — nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
