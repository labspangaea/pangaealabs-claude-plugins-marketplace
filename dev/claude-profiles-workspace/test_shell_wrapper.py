#!/usr/bin/env python3
"""Unit tests for the claude-profiles scripts. Stdlib only.

    python3 dev/claude-profiles-workspace/test_shell_wrapper.py          # from the repo root
    python3 -m unittest discover -s dev/claude-profiles-workspace -p 'test_*.py'

Covers the two things that can damage a real machine, because both have already
happened once:

  * `config_dir()` whitespace handling — a trailing space created a directory
    named '.claude-work  ' on a fresh install, and a leading space is worse,
    since expanduser leaves " ~/..." alone and the path then resolves against
    the current working directory.
  * `shell_wrapper.py` rc editing — a shell startup file is hand-curated and a
    bad edit breaks every future shell, so backup / marker / idempotency are
    asserted rather than assumed.

Everything runs against a temporary HOME. No test touches the real profiles.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "plugins/claude-profiles/skills/setup-claude-profiles/scripts"
sys.path.insert(0, str(SCRIPTS))

from _profiles import config_dir, unusable_profile_dir  # noqa: E402
import shell_wrapper as sw  # noqa: E402


class ConfigDirWhitespace(unittest.TestCase):
    """The bug that created '.claude-work  ' on a fresh install."""

    def test_trailing_space_is_stripped(self):
        self.assertEqual(config_dir("~/.claude-work  "), Path.home() / ".claude-work")

    def test_trailing_tab_is_stripped(self):
        self.assertEqual(config_dir("~/.claude-work\t"), Path.home() / ".claude-work")

    def test_leading_space_still_expands_tilde(self):
        # Without the strip, expanduser leaves " ~/..." untouched and the result
        # is relative to the cwd — a directory literally named '~'.
        self.assertEqual(config_dir(" ~/.claude-work"), Path.home() / ".claude-work")

    def test_blank_means_the_default_profile(self):
        self.assertEqual(config_dir("   "), Path.home() / ".claude")
        self.assertEqual(config_dir(None), Path.home() / ".claude")

    def test_normal_input_is_unchanged(self):
        self.assertEqual(config_dir("~/.claude-work"), Path.home() / ".claude-work")


class UnusableNames(unittest.TestCase):
    def test_unexpanded_tilde_is_rejected(self):
        self.assertIsNotNone(unusable_profile_dir("/tmp/~"))

    def test_padded_name_is_rejected(self):
        self.assertIsNotNone(unusable_profile_dir("/tmp/.claude-work "))

    def test_control_character_is_rejected(self):
        self.assertIsNotNone(unusable_profile_dir("/tmp/.claude\nwork"))

    def test_ordinary_name_is_accepted(self):
        self.assertIsNone(unusable_profile_dir("/tmp/.claude-work"))


class FunctionRendering(unittest.TestCase):
    def test_name_derives_from_the_directory(self):
        self.assertEqual(sw.function_name("/h/.claude-work"), "claude-work")
        self.assertEqual(sw.function_name("/h/.claude-client"), "claude-client")

    def test_bare_claude_dir_gets_a_fallback_name(self):
        self.assertEqual(sw.function_name("/h/.claude"), "claude-alt")

    def test_home_is_collapsed_so_the_block_is_portable(self):
        text = sw.function_text("/h/.claude-work", "/h")
        self.assertIn('CLAUDE_CONFIG_DIR="$HOME/.claude-work"', text)
        self.assertNotIn("/h/.claude-work", text)

    def test_launcher_is_a_function_not_an_alias(self):
        # An alias cannot run the MCP sync before launching.
        self.assertTrue(sw.function_text("/h/.claude-work", "/h").startswith("claude-work() {"))


class ExistingDefinitions(unittest.TestCase):
    def test_alias_is_detected(self):
        self.assertTrue(sw.existing_definitions("alias claude-work='claude'\n", "claude-work")["alias"])

    def test_function_is_detected(self):
        self.assertTrue(sw.existing_definitions("claude-work() {\n}\n", "claude-work")["func"])

    def test_function_keyword_form_is_detected(self):
        self.assertTrue(sw.existing_definitions("function claude-work() {\n}\n", "claude-work")["func"])

    def test_similar_name_is_not_a_false_positive(self):
        self.assertFalse(sw.existing_definitions("claude-worker() {}\n", "claude-work")["func"])


class Splicing(unittest.TestCase):
    def setUp(self):
        self.base = "export PATH=/usr/bin\nalias ll='ls -la'\n"
        self.block = sw.render_block(["/h/.claude-work"], "/h")

    def test_append_preserves_existing_content(self):
        out = sw.splice_block(self.base, self.block)
        self.assertTrue(out.startswith(self.base))
        self.assertIn("claude-work()", out)

    def test_reapplying_is_idempotent(self):
        once = sw.splice_block(self.base, self.block)
        twice = sw.splice_block(once, self.block)
        self.assertEqual(once, twice)
        self.assertEqual(twice.count(sw.BEGIN), 1)

    def test_changed_profile_set_replaces_the_block(self):
        once = sw.splice_block(self.base, self.block)
        grown = sw.splice_block(once, sw.render_block(["/h/.claude-work", "/h/.claude-client"], "/h"))
        self.assertEqual(grown.count(sw.BEGIN), 1)
        self.assertIn("claude-client()", grown)
        self.assertIn("claude-work()", grown)

    def test_append_to_empty_file(self):
        out = sw.splice_block("", self.block)
        self.assertEqual(out.count(sw.BEGIN), 1)


class Planning(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.rc = self.home / ".zshrc"

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_run_is_an_append(self):
        self.rc.write_text("export PATH=/usr/bin\n", encoding="utf-8")
        self.assertEqual(sw.plan(["/h/.claude-work"], self.rc, "/h")["action"], "append")

    def test_second_run_is_an_update(self):
        self.rc.write_text(sw.splice_block("", sw.render_block(["/h/.claude-work"], "/h")), encoding="utf-8")
        self.assertEqual(sw.plan(["/h/.claude-work"], self.rc, "/h")["action"], "update")

    def test_our_own_block_is_not_reported_as_a_clash(self):
        self.rc.write_text(sw.splice_block("", sw.render_block(["/h/.claude-work"], "/h")), encoding="utf-8")
        self.assertEqual(sw.plan(["/h/.claude-work"], self.rc, "/h")["clashes"], [])

    def test_an_alias_clash_is_reported_and_explains_zsh_shadowing(self):
        self.rc.write_text("alias claude-work='claude'\n", encoding="utf-8")
        clashes = sw.plan(["/h/.claude-work"], self.rc, "/h")["clashes"]
        self.assertEqual(len(clashes), 1)
        self.assertIn("alias", clashes[0])

    def test_a_foreign_function_clash_is_reported(self):
        self.rc.write_text("claude-work() { claude; }\n", encoding="utf-8")
        self.assertEqual(len(sw.plan(["/h/.claude-work"], self.rc, "/h")["clashes"]), 1)

    def test_missing_rc_file_is_planned_for_creation(self):
        pl = sw.plan(["/h/.claude-work"], self.rc, "/h")
        self.assertFalse(pl["rc_exists"])
        self.assertEqual(pl["action"], "append")


class Applying(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.rc = self.home / ".zshrc"

    def tearDown(self):
        self.tmp.cleanup()

    def test_apply_writes_and_backs_up(self):
        self.rc.write_text("export PATH=/usr/bin\n", encoding="utf-8")
        backup = sw.apply(sw.plan(["/h/.claude-work"], self.rc, "/h"))
        self.assertIn("claude-work()", self.rc.read_text(encoding="utf-8"))
        self.assertIsNotNone(backup)
        self.assertEqual(Path(backup).read_text(encoding="utf-8"), "export PATH=/usr/bin\n")

    def test_apply_creates_a_missing_rc_without_a_backup(self):
        backup = sw.apply(sw.plan(["/h/.claude-work"], self.rc, "/h"))
        self.assertTrue(self.rc.exists())
        self.assertIsNone(backup)


class CommandLine(unittest.TestCase):
    """The CLI contract the installer wizard parses."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".zshrc").write_text("export PATH=/usr/bin\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        env = dict(os.environ, HOME=str(self.home), SHELL="/bin/zsh")
        env.pop("CLAUDE_CONFIG_DIR", None)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "shell_wrapper.py"), *argv],
            capture_output=True, text=True, env=env,
        )

    def json_of(self, res):
        import json
        return json.loads(res.stdout)

    def test_dry_run_writes_nothing(self):
        before = (self.home / ".zshrc").read_text(encoding="utf-8")
        res = self.run_cli("--to", str(self.home / ".claude-work"), "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.json_of(res)["status"], "dry-run")
        self.assertEqual((self.home / ".zshrc").read_text(encoding="utf-8"), before)

    def test_apply_reports_appended(self):
        res = self.run_cli("--to", str(self.home / ".claude-work"), "--apply", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.json_of(res)["status"], "appended")

    def test_reapply_reports_updated(self):
        self.run_cli("--to", str(self.home / ".claude-work"), "--apply", "--json")
        res = self.run_cli("--to", str(self.home / ".claude-work"), "--apply", "--json")
        self.assertEqual(self.json_of(res)["status"], "updated")

    def test_padded_target_resolves_to_the_clean_name(self):
        res = self.run_cli("--to", str(self.home / ".claude-work") + "  ", "--apply", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        names = [e.name for e in self.home.iterdir()]
        self.assertNotIn(".claude-work  ", names)
        self.assertIn("claude-work", self.json_of(res)["names"][0])

    def test_unsalvageable_name_is_refused(self):
        res = self.run_cli("--to", str(self.home / "~"), "--apply")
        self.assertEqual(res.returncode, 2)
        self.assertIn("Refusing", res.stderr)

    def test_selfcheck_passes(self):
        res = self.run_cli("--selfcheck")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("0 failed", res.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
