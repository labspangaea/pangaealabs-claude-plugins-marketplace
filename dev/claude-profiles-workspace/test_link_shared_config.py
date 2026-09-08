#!/usr/bin/env python3
"""Unit tests for link_shared_config.py — the script that CREATES profile directories.

    python3 -m unittest discover -s dev/claude-profiles-workspace -p 'test_*.py'

These exist because of a gap, not a hunch. `config_dir()`'s whitespace handling was
unit-tested, but the code path that actually makes the directory on disk was only
ever checked by hand in a shell — so nothing guarded the behaviour a user sees.
Every test here runs against a temporary HOME and asserts on the real filesystem
result rather than on a return value.

The shape of the target matters as much as its name: the profile directory must be
a real directory, and the symlinks belong INSIDE it. A profile that is itself a
symlink would make the whole sharing scheme circular.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins/claude-profiles/skills/setup-claude-profiles/scripts"
LINKER = SCRIPTS / "link_shared_config.py"


class LinkerDirectoryCreation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        cfg = self.home / ".claude"
        (cfg / "agents").mkdir(parents=True)
        (cfg / "commands").mkdir(parents=True)
        (cfg / "settings.json").write_text('{"theme":"dark"}\n', encoding="utf-8")
        (cfg / "CLAUDE.md").write_text("# notes\n", encoding="utf-8")
        self.cfg = cfg

    def tearDown(self):
        self.tmp.cleanup()

    def run_linker(self, *argv):
        env = dict(os.environ, HOME=str(self.home))
        env.pop("CLAUDE_CONFIG_DIR", None)
        return subprocess.run(
            [sys.executable, str(LINKER), "--from", str(self.cfg), *argv],
            capture_output=True, text=True, env=env,
        )

    def entries(self):
        return sorted(e.name for e in self.home.iterdir())

    # --- the reported bug -------------------------------------------------
    def test_trailing_space_creates_the_clean_directory(self):
        res = self.run_linker("--to", str(self.home / ".claude-work") + "   ", "--apply")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(".claude-work", self.entries())
        self.assertNotIn(".claude-work   ", self.entries())

    def test_no_entry_anywhere_has_padded_whitespace(self):
        self.run_linker("--to", str(self.home / ".claude-work") + "  ", "--apply")
        for name in self.entries():
            self.assertEqual(name, name.strip(), "entry %r has padded whitespace" % name)

    def test_leading_space_does_not_create_a_tilde_directory(self):
        # " ~/x" defeats expanduser, so the path stops being absolute.
        res = self.run_linker("--to", " ~/.claude-work", "--apply")
        self.assertNotIn("~", self.entries())
        self.assertEqual(res.returncode, 0, res.stderr)

    # --- the shape of what gets created -----------------------------------
    def test_target_is_a_real_directory_not_a_symlink(self):
        target = self.home / ".claude-work"
        self.run_linker("--to", str(target), "--apply")
        self.assertTrue(target.is_dir())
        self.assertFalse(target.is_symlink(), "the profile dir must never itself be a symlink")

    def test_symlinks_are_created_inside_the_target(self):
        target = self.home / ".claude-work"
        self.run_linker("--to", str(target), "--apply")
        links = sorted(e.name for e in target.iterdir() if e.is_symlink())
        self.assertIn("settings.json", links)
        self.assertIn("agents", links)
        self.assertEqual(
            os.path.realpath(target / "settings.json"),
            os.path.realpath(self.cfg / "settings.json"),
        )

    def test_no_symlink_is_created_pointing_at_home(self):
        # The artefact reported from a fresh install was `.claude-work   -> ~`.
        # Nothing this script does should ever produce a link to the home dir.
        self.run_linker("--to", str(self.home / ".claude-work"), "--apply")
        for entry in self.home.iterdir():
            if entry.is_symlink():
                self.assertNotEqual(
                    os.path.realpath(entry), os.path.realpath(self.home),
                    "%s points at HOME" % entry,
                )

    # --- refusals ---------------------------------------------------------
    def test_unsalvageable_name_is_refused_and_creates_nothing(self):
        before = self.entries()
        res = self.run_linker("--to", str(self.home / "~"), "--apply")
        self.assertEqual(res.returncode, 2)
        self.assertIn("Refusing", res.stderr)
        self.assertEqual(self.entries(), before)

    def test_dry_run_creates_nothing(self):
        before = self.entries()
        res = self.run_linker("--to", str(self.home / ".claude-work"))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.entries(), before)
        self.assertFalse((self.home / ".claude-work").exists())

    def test_dry_run_leaves_no_probe_file(self):
        self.run_linker("--to", str(self.home / ".claude-work"))
        self.assertFalse((self.home / ".claude-work").exists())

    # --- reversibility ----------------------------------------------------
    def test_unlink_restores_and_keeps_the_backup(self):
        target = self.home / ".claude-work"
        target.mkdir()
        (target / "settings.json").write_text('{"theme":"light"}\n', encoding="utf-8")
        self.run_linker("--to", str(target), "--apply")
        self.assertTrue((target / "settings.json").is_symlink())

        self.run_linker("--to", str(target), "--unlink", "--apply")
        self.assertFalse((target / "settings.json").is_symlink())
        self.assertEqual(json.loads((target / "settings.json").read_text()), {"theme": "light"})
        backups = list((target / "backups").glob("profile-link-*"))
        self.assertTrue(backups and any(b.iterdir() for b in backups),
                        "the backup must survive the undo so it can be run again")


if __name__ == "__main__":
    unittest.main(verbosity=2)
