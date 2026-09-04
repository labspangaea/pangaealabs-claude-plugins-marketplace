#!/usr/bin/env python3
"""Build a throwaway fake HOME for one eval case.

Every eval runs against one of these instead of the real ~/.claude, so a test
run can never damage a real profile. The scripts under test resolve the default
profile through Path.home(), which honours $HOME, so exporting HOME=<sandbox>
is enough to redirect all of them.

    python3 build_sandbox.py <dest> <scenario>

Scenarios:
  fresh          only a default profile; no second profile yet
  unshared       second profile exists and is signed in, but shares nothing
  shared         second profile fully linked (settings/CLAUDE.md/agents/plugins)
  shared-badline shared, plus a status line script with an email hardcoded in it
  same-account   two profiles signed in to the SAME account
"""

import json
import os
import shutil
import sys
from pathlib import Path

ACCOUNT_A = {
    "emailAddress": "rina@example.com",
    "accountUuid": "aaaaaaaa-1111-4aaa-8aaa-aaaaaaaaaaaa",
    "organizationUuid": "org-aaaa-1111",
    "organizationRateLimitTier": "default_claude_max_5x",
    "billingType": "stripe_subscription",
}
ACCOUNT_B = {
    "emailAddress": "rina@northwind-labs.co",
    "accountUuid": "bbbbbbbb-2222-4bbb-8bbb-bbbbbbbbbbbb",
    "organizationUuid": "org-bbbb-2222",
    "organizationRateLimitTier": "default_claude_max_5x",
    "billingType": "stripe_subscription",
}
MCP = {
    "postgres-lsp": {"type": "stdio", "command": "node", "args": ["/opt/mcp/pg/index.js"], "env": {}},
    "context7": {"type": "stdio", "command": "npx", "args": ["-y", "@upstash/context7-mcp"], "env": {}},
    "linear": {"type": "http", "url": "https://mcp.linear.app/mcp"},
}
SETTINGS = {
    "env": {"EDITOR": "nvim"},
    "permissions": {"allow": ["Bash(git:*)", "Bash(python3:*)"], "defaultMode": "auto"},
    "model": "opus",
    "effortLevel": "high",
    "theme": "dark",
    "statusLine": {"type": "command", "command": "bash __HOME__/.claude/statusline.sh"},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "audit-hook"}]}]},
    "enabledPlugins": {
        "docsmith@pangaealabs-claude-plugins-marketplace": True,
        "notes-cli@sidecar-tools": True,
    },
    "extraKnownMarketplaces": {
        "pangaealabs-claude-plugins-marketplace": {
            "source": {"source": "github", "repo": "labspangaea/pangaealabs-claude-plugins-marketplace"}
        }
    },
}
STATUSLINE = """#!/bin/sh
# --- ACCOUNT CONFIGURATION ---
ACCOUNT_EMAIL="rina@example.com"
SUBS_PLAN="Max"
# -----------------------------
input=$(cat)
printf '%s [%s]\\n' "$ACCOUNT_EMAIL" "$SUBS_PLAN"
"""


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_default_profile(home):
    cfg = home / ".claude"
    (cfg / "agents").mkdir(parents=True, exist_ok=True)
    (cfg / "commands").mkdir(parents=True, exist_ok=True)
    (cfg / "skills").mkdir(parents=True, exist_ok=True)
    (cfg / "plugins" / "marketplaces").mkdir(parents=True, exist_ok=True)

    settings = json.loads(json.dumps(SETTINGS).replace("__HOME__", str(home)))
    write_json(cfg / "settings.json", settings)
    (cfg / "CLAUDE.md").write_text("# my notes\n\n@style.md\n", encoding="utf-8")
    (cfg / "style.md").write_text("Prefer short commit messages.\n", encoding="utf-8")
    (cfg / "agents" / "researcher.md").write_text("---\nname: researcher\n---\nresearch things\n", encoding="utf-8")
    (cfg / "commands" / "standup.md").write_text("Summarise yesterday.\n", encoding="utf-8")
    (cfg / "statusline.sh").write_text(STATUSLINE, encoding="utf-8")
    os.chmod(cfg / "statusline.sh", 0o755)

    # The marketplace registry is deliberately split: 'sidecar-tools' exists ONLY
    # here, not in settings.json's extraKnownMarketplaces.
    write_json(cfg / "plugins" / "known_marketplaces.json", {
        "pangaealabs-claude-plugins-marketplace": {
            "source": {"source": "github", "repo": "labspangaea/pangaealabs-claude-plugins-marketplace"},
            "installLocation": str(cfg / "plugins" / "marketplaces" / "pangaealabs"),
        },
        "sidecar-tools": {
            "source": {"source": "github", "repo": "someone/sidecar-tools"},
            "installLocation": str(cfg / "plugins" / "marketplaces" / "sidecar-tools"),
        },
    })
    write_json(cfg / "plugins" / "installed_plugins.json", {
        "version": 2,
        "plugins": {
            "docsmith@pangaealabs-claude-plugins-marketplace": {"version": "1.0.0"},
            "notes-cli@sidecar-tools": {"version": "0.3.1"},
        },
    })

    # The DEFAULT profile's live config is ~/.claude.json ...
    write_json(home / ".claude.json", {
        "numStartups": 214,
        "installMethod": "native",
        "oauthAccount": ACCOUNT_A,
        "mcpServers": MCP,
        "projects": {str(home / "code" / "api"): {"hasTrustDialogAccepted": True}},
    })
    # ... and this stale leftover must NOT be mistaken for it.
    write_json(cfg / ".claude.json", {
        "numStartups": 3,
        "oauthAccount": dict(ACCOUNT_A, emailAddress="old-address@example.com"),
        "mcpServers": {},
    })
    return cfg


def build_second_profile(home, account, with_mcp=False):
    work = home / ".claude-work"
    work.mkdir(parents=True, exist_ok=True)
    (work / "plugins").mkdir(exist_ok=True)
    write_json(work / "plugins" / "known_marketplaces.json", {})
    write_json(work / "plugins" / "installed_plugins.json", {"version": 2, "plugins": {}})
    write_json(work / ".claude.json", {
        "numStartups": 4,
        "oauthAccount": account,
        "mcpServers": dict(MCP) if with_mcp else {},
        "projects": {},
    })
    write_json(work / "settings.json", {"theme": "dark"})
    (work / ".credentials.json").write_text('{"token":"fake-not-a-real-token"}\n', encoding="utf-8")
    os.chmod(work / ".credentials.json", 0o600)
    return work


def share(home, work, entries=("settings.json", "CLAUDE.md", "style.md", "agents", "commands", "plugins", "skills")):
    cfg = home / ".claude"
    backups = work / "backups" / "profile-link-20260101-000000"
    for name in entries:
        src, dst = cfg / name, work / name
        if not src.exists():
            continue
        if dst.exists() and not dst.is_symlink():
            backups.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(backups / name))
        elif dst.is_symlink():
            dst.unlink()
        dst.symlink_to(src, target_is_directory=src.is_dir())


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    dest, scenario = Path(sys.argv[1]).resolve(), sys.argv[2]
    if dest.exists():
        shutil.rmtree(dest)
    home = dest / "home"
    home.mkdir(parents=True)
    (home / "code" / "api").mkdir(parents=True)

    build_default_profile(home)

    if scenario == "fresh":
        pass
    elif scenario == "unshared":
        build_second_profile(home, ACCOUNT_B)
    elif scenario in ("shared", "shared-badline"):
        work = build_second_profile(home, ACCOUNT_B, with_mcp=True)
        share(home, work)
    elif scenario == "same-account":
        build_second_profile(home, ACCOUNT_A)
    else:
        print("unknown scenario %r" % scenario)
        return 2

    print("built %s sandbox at %s" % (scenario, home))
    return 0


if __name__ == "__main__":
    sys.exit(main())
