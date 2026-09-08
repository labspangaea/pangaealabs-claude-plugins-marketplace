#!/usr/bin/env python3
"""Machine-check the assertions that are about filesystem state, not prose.

    python3 grade_state.py iteration-1

Prose assertions ("explains why X") still need a reading pass — those are graded
by the grader agent. Everything here is checkable without judgement, so it is
checked the same way every iteration and cannot drift.

Emits state_checks.json into each run directory.
"""

import json
import os
import sys
from pathlib import Path

SNAPSHOT = Path(__file__).with_name("real_profiles_snapshot.json")


def is_link(p):
    return Path(p).is_symlink()


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def real_profiles_untouched():
    """Compare the real ~/.claude and ~/.claude-work against the pre-run snapshot."""
    import hashlib
    want = load(SNAPSHOT) or {}
    drift = []
    for path, digest in want.items():
        p = Path(path)
        if not p.exists() and not p.is_symlink():
            drift.append("missing: " + path)
            continue
        try:
            # Resolve through symlinks, exactly as the snapshot did - a shared
            # entry is a symlink whose CONTENT is what we care about.
            now = hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else \
                  ("link:" + os.readlink(p))
        except OSError as exc:
            drift.append("unreadable: %s (%s)" % (path, exc))
            continue
        if now != digest:
            drift.append("changed: " + path)
    return (not drift), ("no drift in %d tracked files" % len(want)) if not drift else "; ".join(drift)


def checks_for(eval_id, home):
    """Machine-verifiable assertions, keyed to the iteration-2 assertion texts.

    Each tuple is (assertion text VERBATIM, passed, evidence). The text must
    match evals.json exactly or the grader cannot merge the verdict.
    """
    cfg, work = home / ".claude", home / ".claude-work"
    out = []
    links = {p.name: p for p in work.glob("*") if p.is_symlink()} if work.is_dir() else {}

    if eval_id == 0:
        out.append((
            "Leaves the user's existing default profile where it is - does not relocate ~/.claude or require re-logging-in to it",
            (cfg / "settings.json").is_file() and not (cfg / "settings.json").is_symlink()
            and (home / ".claude.json").is_file(),
            "default settings.json real=%s; ~/.claude.json present=%s; sibling profiles=%s"
            % (not (cfg / "settings.json").is_symlink(), (home / ".claude.json").is_file(),
               sorted(d.name for d in home.glob(".claude-*") if d.is_dir()) or "none"),
        ))
        out.append((
            "Second profile ends up sharing config through live symlinks, not one-time copies that will drift",
            len(links) >= 4,
            "symlinks in second profile: %s" % (sorted(links) or "none"),
        ))

    if eval_id == 1:
        wj = load(work / ".claude.json") or {}
        servers = sorted((wj.get("mcpServers") or {}).keys())
        out.append((
            "Work profile's .claude.json ends up containing all 3 MCP servers (context7, linear, postgres-lsp)",
            servers == ["context7", "linear", "postgres-lsp"],
            "mcpServers = %s" % (servers or "none"),
        ))
        email = (wj.get("oauthAccount") or {}).get("emailAddress")
        out.append((
            "Work profile's own account rina@northwind-labs.co is preserved, not overwritten by the personal account",
            email == "rina@northwind-labs.co",
            "oauthAccount.emailAddress = %r" % email,
        ))
        reg = load(work / "plugins" / "known_marketplaces.json") or {}
        promoted = (load(work / "settings.json") or {}).get("extraKnownMarketplaces") or {}
        out.append((
            "The work profile learns about the sidecar-tools marketplace, which exists only in plugins/known_marketplaces.json",
            "sidecar-tools" in reg or "sidecar-tools" in promoted,
            "registry=%s; settings.extraKnownMarketplaces=%s"
            % (sorted(reg) or "empty", sorted(promoted) or "empty"),
        ))
        out.append((
            "That fix is DURABLE - plugins/ is shared live, so a plugin installed later appears in both, rather than a copy taken once",
            (work / "plugins").is_symlink(),
            "work/plugins is %s" % ("a live symlink" if (work / "plugins").is_symlink()
                                    else "a real directory (snapshot copy)"),
        ))

    if eval_id == 4:
        st = work / "settings.json"
        out.append((
            "The work profile's settings.json ends up a real file, not a symlink",
            st.is_file() and not st.is_symlink(),
            "exists=%s symlink=%s" % (st.exists(), st.is_symlink()),
        ))
        body = load(st)
        out.append((
            "Restores the work profile's pre-link settings.json from its backups directory",
            isinstance(body, dict) and body.get("theme") == "dark" and "permissions" not in body,
            "content = %s" % json.dumps(body)[:120],
        ))
        out.append((
            "Accounts for ALL seven shared entries, not just settings.json - none is left dangling or silently dropped",
            not links,
            "symlinks still present: %s" % (sorted(links) or "none"),
        ))
        pre = sorted((work / "backups").glob("profile-link-*")) if (work / "backups").is_dir() else []
        survived = any(any(d.iterdir()) for d in pre)
        out.append((
            "The backup directory survives the undo, so the operation can be run again",
            survived,
            "pre-link backups: %s" % ({d.name: sorted(x.name for x in d.iterdir()) for d in pre} or "none"),
        ))
        ds = cfg / "settings.json"
        out.append((
            "The default profile is left intact - ~/.claude/settings.json still exists and is not a symlink",
            ds.is_file() and not ds.is_symlink(),
            "exists=%s symlink=%s" % (ds.exists(), ds.is_symlink()),
        ))
        out.append((
            "Does not delete the shared source files in the default profile",
            all((cfg / n).exists() for n in ("CLAUDE.md", "agents", "commands", "plugins")),
            "present: %s" % [n for n in ("CLAUDE.md", "agents", "commands", "plugins") if (cfg / n).exists()],
        ))

    ok, detail = real_profiles_untouched()
    out.append(("Leaves the real /Users/harry/.claude and /Users/harry/.claude-work untouched", ok, detail))
    return out


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "iteration-1").resolve()
    # A grader that checks nothing must not read as a pass. The path is relative
    # to the cwd, so running this from the repo root instead of the workspace
    # silently globbed zero run directories and printed "0/0 passed" — exactly
    # the looks-like-success failure this plugin exists to catch.
    if not root.is_dir():
        print("no such iteration directory: %s" % root, file=sys.stderr)
        return 2
    total = passed = 0
    for run in sorted(root.glob("eval-*/*/")):
        meta = load(run / "eval_metadata.json")
        if not meta:
            continue
        home = run / "sandbox" / "home"
        if not home.is_dir():
            continue
        results = checks_for(meta["eval_id"], home)
        (run / "state_checks.json").write_text(json.dumps([
            {"text": t, "passed": bool(p), "evidence": e} for t, p, e in results
        ], indent=2) + "\n", encoding="utf-8")
        for t, p, e in results:
            total += 1
            passed += 1 if p else 0
            flag = "PASS" if p else "FAIL"
            print("%-4s %-28s %s" % (flag, run.parent.name + "/" + run.name, t[:70]))
            if not p:
                print("       evidence: %s" % e)
    if total == 0:
        print("no run directories under %s — nothing was checked." % root, file=sys.stderr)
        return 2
    print("\nstate checks: %d/%d passed" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
