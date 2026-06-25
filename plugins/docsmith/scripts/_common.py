"""Shared helpers for the docsmith scripts (build.py, setup_profile.py).

Lives in scripts/ so it travels with the relocatable make-pdf bundle — the installer
copies scripts/ wholesale into the universal store, so a sibling import resolves both
from the plugin layout and from the standalone ~/.agents/skills layout.
"""
from __future__ import annotations

import os
from pathlib import Path


def docsmith_home() -> Path:
    """Resolve the docsmith home dir (honours $DOCSMITH_HOME, default ~/.docsmith)."""
    return Path(os.environ.get("DOCSMITH_HOME", Path.home() / ".docsmith"))
