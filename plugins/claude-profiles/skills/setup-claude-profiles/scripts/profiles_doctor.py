#!/usr/bin/env python3
"""Report the state of every Claude Code profile on this machine. Read-only.

    python3 profiles_doctor.py                        # default profile + any ~/.claude-*
    python3 profiles_doctor.py ~/.claude ~/.claude-work
    python3 profiles_doctor.py --json

Reports, per profile: the config dir and its .claude.json, the signed-in
account and plan, where the OAuth token is stored, which shareable entries are
symlinks (and to where), MCP server count, and the platform hazards that break
this setup — a config dir on a Windows filesystem under WSL, a filesystem that
will not hold a symlink, or a world-readable credentials file.

Nothing is written. Run it before and after link_shared_config.py.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _profiles import (  # noqa: E402
    DEFAULT_CONFIG_DIR,
    SHAREABLE,
    account_of,
    claude_binary,
    config_dir,
    config_json_for,
    credentials_state,
    filesystem_of,
    host_platform,
    imported_memory_files,
    is_windows_filesystem,
    symlinks_work_in,
)


def discover_profiles():
    """The default profile plus every sibling ~/.claude-* that looks like one."""
    found = []
    if DEFAULT_CONFIG_DIR.is_dir():
        found.append(DEFAULT_CONFIG_DIR)
    home = Path.home()
    for entry in sorted(home.glob(".claude-*")):
        if entry.is_dir() and (entry / ".claude.json").exists():
            found.append(entry)
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        resolved = config_dir(env)
        if resolved not in found and resolved.is_dir():
            found.append(resolved)
    return found


def link_report(cfg_dir, extra_names=()):
    """For each shareable entry: missing / own / link -> target / broken link."""
    out = {}
    for name in list(SHAREABLE) + [n for n in extra_names if n not in SHAREABLE]:
        path = Path(cfg_dir) / name
        if path.is_symlink():
            target = os.readlink(str(path))
            out[name] = {
                "kind": "link",
                "target": target,
                "resolves": path.exists(),
            }
        elif path.exists():
            out[name] = {"kind": "own", "target": None, "resolves": True}
        else:
            out[name] = {"kind": "missing", "target": None, "resolves": False}
    return out


def inspect(cfg_dir):
    cfg_dir = Path(cfg_dir)
    acct = account_of(cfg_dir)
    creds = credentials_state(cfg_dir)
    sym_ok, sym_detail = symlinks_work_in(cfg_dir)
    claude_md = cfg_dir / "CLAUDE.md"
    imports = imported_memory_files(claude_md)
    return {
        "config_dir": str(cfg_dir),
        "is_default": cfg_dir == DEFAULT_CONFIG_DIR,
        "config_json": str(config_json_for(cfg_dir)),
        "config_json_exists": config_json_for(cfg_dir).exists(),
        "account": acct,
        "credentials": {
            "store": creds["store"],
            "path": str(creds["path"]) if creds["path"] else None,
            "present": bool(creds["path"] and creds["path"].exists()) if creds["path"] else None,
            "warning": creds["warning"],
        },
        "links": link_report(cfg_dir, imports),
        "memory_imports": imports,
        "filesystem": filesystem_of(cfg_dir),
        "on_windows_filesystem": is_windows_filesystem(cfg_dir),
        "symlinks_supported": sym_ok,
        "symlinks_detail": sym_detail,
    }


def hazards(host, profiles):
    """Problems that will actually break the setup, worst first."""
    out = []
    for p in profiles:
        cfg = p["config_dir"]
        if p["on_windows_filesystem"]:
            out.append(
                "%s sits on a Windows filesystem (%s). Move it onto the Linux "
                "filesystem (e.g. ~/.claude-work): symlink sharing and the 0600 "
                "mode on .credentials.json do not survive there." % (cfg, p["filesystem"])
            )
        elif not p["symlinks_supported"]:
            out.append(
                "%s cannot hold a symlink (%s) — config sharing will not work there."
                % (cfg, p["symlinks_detail"])
            )
        if not p["config_json_exists"]:
            out.append("%s has no %s — the profile has never been started." % (cfg, p["config_json"]))
        elif not p["account"]["logged_in"]:
            out.append(
                "%s is not signed in. Run: CLAUDE_CONFIG_DIR=%s claude  then /login"
                % (cfg, cfg)
            )
        if p["credentials"]["warning"]:
            out.append(p["credentials"]["warning"])
        links = p["links"]
        broken = [n for n, v in links.items() if v["kind"] == "link" and not v["resolves"]]
        if broken:
            out.append("%s has dangling symlinks: %s" % (cfg, ", ".join(sorted(broken))))
        if links.get("CLAUDE.md", {}).get("kind") == "link" and p["memory_imports"]:
            missing = [
                n for n in p["memory_imports"]
                if not (Path(cfg) / n).exists()
            ]
            if missing:
                out.append(
                    "%s links CLAUDE.md but not the files it imports (%s) — "
                    "those @-imports will not resolve." % (cfg, ", ".join(missing))
                )

    emails = [p["account"]["email"] for p in profiles if p["account"]["email"]]
    dupes = {e for e in emails if emails.count(e) > 1}
    for email in sorted(dupes):
        out.append(
            "More than one profile is signed in as %s — those profiles share a "
            "subscription and its rate limits, which defeats the point." % email
        )
    if host == "windows":
        out.append(
            "Running on native Windows. This setup is written for macOS, Linux and "
            "WSL; symlink creation on Windows needs Developer Mode or an elevated shell."
        )
    return out


def render(host, profiles, binary):
    lines = []
    lines.append("Claude Code profiles — %s" % host)
    lines.append("claude binary: %s" % (binary or "NOT FOUND on PATH"))
    if host == "wsl" and binary and binary.startswith("/mnt/"):
        lines.append(
            "  ! that is the Windows build seen through /mnt. Install Claude Code "
            "inside the distro so profiles live on the Linux filesystem."
        )
    lines.append("")
    for p in profiles:
        acct = p["account"]
        who = acct["email"] or "(not signed in)"
        lines.append("%s%s" % (p["config_dir"], "   [default]" if p["is_default"] else ""))
        lines.append("  account      %s  [%s]" % (who, acct["plan"]))
        lines.append("  config json  %s%s" % (p["config_json"], "" if p["config_json_exists"] else "   MISSING"))
        lines.append("  credentials  %s" % p["credentials"]["store"])
        lines.append("  mcp servers  %d%s" % (
            len(acct["mcp_servers"]),
            ("  (" + ", ".join(acct["mcp_servers"]) + ")") if acct["mcp_servers"] else "",
        ))
        lines.append("  filesystem   %s%s" % (
            p["filesystem"] or ("n/a (only reported on Linux/WSL)" if host in ("macos", "windows") else "unknown"),
            "  ON A WINDOWS DRIVE" if p["on_windows_filesystem"] else "",
        ))
        shared, own, missing = [], [], []
        for name, v in p["links"].items():
            if v["kind"] == "link":
                shared.append("%s -> %s%s" % (name, v["target"], "" if v["resolves"] else " (BROKEN)"))
            elif v["kind"] == "own":
                own.append(name)
            else:
                missing.append(name)
        lines.append("  shared       %s" % ("; ".join(shared) if shared else "(none)"))
        lines.append("  own copy     %s" % (", ".join(own) if own else "(none)"))
        lines.append("  absent       %s" % (", ".join(missing) if missing else "(none)"))
        if p["memory_imports"]:
            lines.append("  CLAUDE.md imports  %s" % ", ".join(p["memory_imports"]))
        lines.append("")

    problems = hazards(host, profiles)
    if problems:
        lines.append("Problems (%d):" % len(problems))
        for item in problems:
            lines.append("  - %s" % item)
    else:
        lines.append("No problems found.")
    return "\n".join(lines)


WSL_MOUNTS = """\
/dev/sdc / ext4 rw,relatime 0 0
drivers /usr/lib/wsl/drivers 9p ro,dirsync 0 0
C:\\ /mnt/c 9p rw,dirsync,noatime 0 0
D:\\ /mnt/d drvfs rw,noatime 0 0
"""


def selfcheck():
    """Assert the rules this plugin depends on, including the WSL paths.

    The WSL filesystem checks are driven from a captured /proc/mounts table so
    they run — and can fail — on macOS too, where /proc does not exist.
    """
    import tempfile
    from _profiles import filesystem_of, is_windows_filesystem

    failures, ran = [], []

    def check(label, got, want):
        ran.append(label)
        if got != want:
            failures.append("%s: got %r, want %r" % (label, got, want))

    # The config-json rule: the default profile is the special case.
    check("default profile json", config_json_for(DEFAULT_CONFIG_DIR), Path.home() / ".claude.json")
    check("named profile json",
          config_json_for(Path.home() / ".claude-work"),
          Path.home() / ".claude-work" / ".claude.json")

    # WSL: /mnt/* is a Windows drive; the Linux home is not.
    check("wsl /mnt/c fstype", filesystem_of("/mnt/c/Users/me/.claude", WSL_MOUNTS), "9p")
    check("wsl /mnt/d fstype", filesystem_of("/mnt/d/claude", WSL_MOUNTS), "drvfs")
    check("wsl /mnt/c is windows", is_windows_filesystem("/mnt/c/Users/me/.claude", WSL_MOUNTS), True)
    check("wsl /mnt/d is windows", is_windows_filesystem("/mnt/d/claude", WSL_MOUNTS), True)
    check("wsl ext4 root not windows", is_windows_filesystem("/root/.claude-work", WSL_MOUNTS), False)
    # A path under /usr/lib/wsl is 9p but is not a user drive; still flagged,
    # which is correct — nobody should put a config dir there either.
    check("longest-prefix wins", filesystem_of("/usr/lib/wsl/drivers/x", WSL_MOUNTS), "9p")

    # @-imports beside a CLAUDE.md are discovered; paths outside are not.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "CLAUDE.md").write_text("@RTK.md\n@../escape.md\n@missing.md\n", encoding="utf-8")
        (d / "RTK.md").write_text("x", encoding="utf-8")
        check("memory imports", imported_memory_files(d / "CLAUDE.md"), ["RTK.md"])
        ok, _ = symlinks_work_in(d)
        check("symlink probe on a normal dir", ok, True)

    for line in failures:
        print("FAIL " + line)
    print("selfcheck: %d passed, %d failed" % (len(ran) - len(failures), len(failures)))
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config_dirs", nargs="*", help="profiles to inspect (default: auto-discover)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selfcheck", action="store_true", help="test the platform rules and exit")
    args = ap.parse_args(argv)

    if args.selfcheck:
        return selfcheck()

    dirs = [config_dir(d) for d in args.config_dirs] if args.config_dirs else discover_profiles()
    if not dirs:
        print("No Claude Code profile found. Expected ~/.claude to exist.", file=sys.stderr)
        return 1

    host = host_platform()
    profiles = [inspect(d) for d in dirs]
    binary = claude_binary()

    if args.json:
        print(json.dumps(
            {"platform": host, "claude_binary": binary, "profiles": profiles,
             "problems": hazards(host, profiles)},
            indent=2,
        ))
    else:
        print(render(host, profiles, binary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
