"""Shared helpers for the setup-claude-profiles scripts.

Python 3.8+, standard library only. Nothing here mutates state — the write
operations live in link_shared_config.py and sync_mcp.py.

The one rule every caller needs
-------------------------------
A Claude Code *profile* is a config directory. The DEFAULT profile is
``~/.claude``, and any other profile is selected by exporting
``CLAUDE_CONFIG_DIR``. But the JSON file holding the account and the MCP
servers is NOT in the same place for both:

    default profile   ->  ~/.claude.json          (NOT ~/.claude/.claude.json)
    CLAUDE_CONFIG_DIR ->  $CLAUDE_CONFIG_DIR/.claude.json

``~/.claude/.claude.json`` may also exist as a stale leftover on older
installs; reading it instead of ``~/.claude.json`` silently reports the wrong
account. ``config_json_for()`` encodes the rule — always go through it.
"""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".claude"

# Entries that can be shared between profiles by symlink. Everything absent
# from this list is either per-account state (sessions, history, projects) or
# the account file itself, and must stay separate.
SHAREABLE = ["settings.json", "CLAUDE.md", "agents", "commands", "plugins", "skills"]

# Filesystem types that are a Windows drive seen from WSL. Symlinks and Unix
# permission bits are unreliable on these, which breaks both the symlink
# sharing and the 0600 mode on .credentials.json.
WINDOWS_FS_TYPES = {"drvfs", "9p", "v9fs", "cifs", "smbfs"}


def config_dir(value=None):
    """Resolve a profile's config directory. None/'' means the default profile.

    Whitespace is stripped before anything else, and that is load-bearing rather
    than tidiness. A TRAILING space produced a real directory named
    ``.claude-work  `` that nobody could type again; a LEADING space is worse,
    because ``expanduser`` leaves " ~/..." alone, so the path stops being
    absolute and resolves against the current working directory — creating a
    folder literally named ``~`` wherever the command happened to run.
    """
    if value is None or not str(value).strip():
        return DEFAULT_CONFIG_DIR
    path = Path(os.path.expanduser(str(value).strip()))
    if path.name != path.name.strip():
        path = path.parent / path.name.strip()
    return path.resolve(strict=False)


def unusable_profile_dir(path):
    """Why `path` is a bad config directory, or None if it is fine.

    Callers that CREATE the directory check this first: a name that cannot be
    typed back is worse to create than to refuse.
    """
    name = Path(path).name
    if not name:
        return "resolves to a filesystem root"
    if name != name.strip():
        return "name has leading or trailing whitespace (%r) — almost always a typo" % name
    if name == "~":
        return ("name is literally '~' — the tilde was not expanded, usually a quoted or "
                "space-prefixed argument, and this would be created in the current directory")
    if any(ord(c) < 32 for c in name):
        return "name contains a control character (%r)" % name
    return None


def config_json_for(cfg_dir):
    """Path of the .claude.json that belongs to this config dir.

    See the module docstring — the default profile is the special case.
    """
    cfg_dir = Path(cfg_dir)
    if cfg_dir == DEFAULT_CONFIG_DIR:
        return Path.home() / ".claude.json"
    return cfg_dir / ".claude.json"


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {} if default is None else default


def write_json_atomic(path, data, mode=0o600):
    """Replace `path` with `data`, never leaving a truncated file behind."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
        os.chmod(path, mode)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def account_of(cfg_dir):
    """Account summary for a profile, read from its .claude.json.

    `oauthAccount` being present is the practical "is this profile logged in"
    signal, and reading it never touches the OS keychain — so this stays quiet
    and never triggers a macOS keychain-access prompt.
    """
    data = read_json(config_json_for(cfg_dir))
    acct = data.get("oauthAccount") or {}
    tier = acct.get("organizationRateLimitTier") or ""
    if "team" in tier:
        plan = "Team"
    elif "pro" in tier:
        plan = "Pro"
    elif "max" in tier:
        plan = "Max"
    else:
        plan = tier or "unknown"
    return {
        "email": acct.get("emailAddress"),
        "account_uuid": acct.get("accountUuid"),
        "org_uuid": acct.get("organizationUuid"),
        "plan": plan,
        "tier": tier,
        "logged_in": bool(acct.get("accountUuid")),
        "mcp_servers": sorted((data.get("mcpServers") or {}).keys()),
    }


def host_platform():
    """'macos', 'wsl', 'linux' or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if os.environ.get("WSL_DISTRO_NAME"):
        return "wsl"
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="replace") as fh:
            if "microsoft" in fh.read().lower():
                return "wsl"
    except OSError:
        pass
    return "linux"


def _mounts(source=None):
    """Parsed /proc/mounts as [(mountpoint, fstype)]. `source` is for tests."""
    if source is not None:
        rows = []
        for line in source.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                rows.append((parts[1], parts[2]))
        return rows
    try:
        with open("/proc/mounts", "r", encoding="utf-8", errors="replace") as fh:
            rows = []
            for line in fh:
                parts = line.split()
                if len(parts) >= 3:
                    rows.append((parts[1], parts[2]))
            return rows
    except OSError:
        return []


def filesystem_of(path, mounts=None):
    """Filesystem type backing `path`, or None when it cannot be determined.

    Used to catch a config directory placed under /mnt/c on WSL, where symlinks
    and permission bits do not survive.
    """
    path = str(Path(path).resolve(strict=False))
    best, best_type = "", None
    for mount, fstype in _mounts(mounts):
        if (path == mount or path.startswith(mount.rstrip("/") + "/")) and len(mount) > len(best):
            best, best_type = mount, fstype
    return best_type


def is_windows_filesystem(path, mounts=None):
    fstype = filesystem_of(path, mounts)
    return fstype is not None and fstype in WINDOWS_FS_TYPES


def symlinks_work_in(directory):
    """Actually create and remove a symlink to prove the filesystem allows it.

    Cheaper than reasoning about WSL versions and mount options: just try it.
    Returns (ok: bool, detail: str).
    """
    directory = Path(directory)
    if not directory.is_dir():
        return False, "directory does not exist"
    probe = directory / ".claude-profiles-symlink-probe"
    try:
        if probe.is_symlink() or probe.exists():
            probe.unlink()
        probe.symlink_to(directory)
        ok = probe.is_symlink()
        probe.unlink()
        return ok, "ok" if ok else "symlink created but not detected as one"
    except OSError as exc:
        try:
            if probe.is_symlink():
                probe.unlink()
        except OSError:
            pass
        return False, str(exc)


def credentials_state(cfg_dir):
    """Where this profile's OAuth token lives, and whether it looks healthy.

    macOS keeps it in the login keychain under a per-config-dir service name, so
    there is no file to inspect and we deliberately do not query the keychain
    (that can raise an access prompt). Everywhere else it is a file in the
    config dir that must not be world-readable.
    """
    host = host_platform()
    if host == "macos":
        return {
            "store": "macOS keychain (service 'Claude Code-credentials[-<hash>]', one per config dir)",
            "path": None,
            "warning": None,
        }
    path = Path(cfg_dir) / ".credentials.json"
    warning = None
    if path.exists():
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            warning = "%s is mode %o — should be 600 (readable by other users)" % (path, mode)
    return {"store": "file", "path": path, "warning": warning}


def claude_binary():
    """Absolute path of the `claude` on PATH, or None."""
    try:
        out = subprocess.run(
            ["command", "-v", "claude"],
            capture_output=True, text=True, timeout=10,
            executable="/bin/sh", shell=False, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        out = None
    if out is None or out.returncode != 0 or not out.stdout.strip():
        for d in os.environ.get("PATH", "").split(os.pathsep):
            candidate = Path(d) / "claude"
            if candidate.is_file() and os.access(str(candidate), os.X_OK):
                return str(candidate)
        return None
    return out.stdout.strip()


def imported_memory_files(claude_md):
    """The `@file.md` imports a CLAUDE.md pulls in from its own directory.

    An `@`-import resolves next to the CLAUDE.md, so linking CLAUDE.md alone
    leaves the import dangling in the second profile. Callers link these too.
    """
    claude_md = Path(claude_md)
    if not claude_md.is_file():
        return []
    found = []
    try:
        text = claude_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    for token in text.split():
        if token.startswith("@") and token.endswith(".md"):
            name = token[1:]
            if "/" not in name and ".." not in name:
                found.append(name)
    seen, out = set(), []
    for name in found:
        if name not in seen and (claude_md.parent / name).is_file():
            seen.add(name)
            out.append(name)
    return out
