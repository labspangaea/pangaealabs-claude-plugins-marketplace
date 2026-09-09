"""Tests for publish-session / consume-session.

Everything runs against a temporary HOME and a temporary shared directory, so a
failing test can never touch the real profiles under ~/.claude*.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "plugins" / "claude-profiles" / "skills"
PUBLISH = SKILLS / "publish-session" / "scripts" / "publish_session.py"
CONSUME = SKILLS / "consume-session" / "scripts" / "consume_session.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def transcript(cwd="/Users/x/proj", nonce=None, extra=()):
    """A miniature but structurally faithful transcript."""
    lines = [
        {"type": "user", "cwd": cwd, "gitBranch": "main",
         "message": {"content": f"fix the seed script\n<system-reminder>ignore me</system-reminder>"}},
        {"type": "assistant", "cwd": cwd, "message": {"content": [
            {"type": "thinking", "thinking": "SECRET-THOUGHT"},
            {"type": "text", "text": "Looking at the seeds now."},
            {"type": "tool_use", "name": "Bash", "input": {"description": "run the seeder"}},
        ]}},
        {"type": "user", "cwd": cwd, "message": {"content": [
            {"type": "tool_result", "content": "HUGE-TOOL-OUTPUT" * 100},
        ]}},
        {"type": "assistant", "isSidechain": True, "cwd": cwd,
         "message": {"content": [{"type": "text", "text": "SUBAGENT-CHATTER"}]}},
        {"type": "assistant", "cwd": cwd, "message": {"content": [
            {"type": "text", "text": f"Done. {nonce or ''}"}]}},
    ]
    return "\n".join(json.dumps(x) for x in list(lines) + list(extra)) + "\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.shared = self.home / "shared"
        self.env = {**os.environ,
                    "HOME": str(self.home),
                    "CLAUDE_CONFIG_DIR": str(self.home / ".claude"),
                    "CLAUDE_SHARED_SESSIONS_DIR": str(self.shared)}
        self.addCleanup(self.tmp.cleanup)

    def write_session(self, sid, **kw):
        proj = self.home / ".claude" / "projects" / "-Users-x-proj"
        proj.mkdir(parents=True, exist_ok=True)
        f = proj / f"{sid}.jsonl"
        f.write_text(transcript(**kw))
        return f

    def run_script(self, script, *args, expect=0):
        r = subprocess.run([sys.executable, str(script), *args],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, expect, f"stdout={r.stdout}\nstderr={r.stderr}")
        return r


class TestPublish(Base):
    def test_finds_current_session_by_nonce_not_by_mtime(self):
        old = self.write_session("aaaa", nonce="NONCE-XYZ")
        newer = self.write_session("bbbb")            # written later -> newest mtime
        os.utime(newer, (9e8 + 1000, 9e8 + 1000))
        os.utime(old, (9e8, 9e8))
        self.run_script(PUBLISH, "--nonce", "NONCE-XYZ")
        self.assertTrue((self.shared / "aaaa.jsonl").exists(), "picked the wrong session")
        self.assertFalse((self.shared / "bbbb.jsonl").exists())

    def test_missing_nonce_fails_loudly(self):
        self.write_session("aaaa")
        r = self.run_script(PUBLISH, "--nonce", "NOT-PRESENT", expect=1)
        self.assertIn("No transcript contains", r.stderr)

    def test_source_is_left_untouched(self):
        src = self.write_session("aaaa", nonce="N1")
        before = src.read_bytes()
        self.run_script(PUBLISH, "--nonce", "N1")
        self.assertEqual(src.read_bytes(), before)


class TestDigest(Base):
    def digest(self, sid="aaaa", **kw):
        src = self.write_session(sid, **kw)
        self.shared.mkdir(parents=True, exist_ok=True)
        (self.shared / src.name).write_bytes(src.read_bytes())
        self.run_script(CONSUME, "digest", sid)
        return (self.shared / f"{sid}.digest.md").read_text()

    def test_keeps_conversation_drops_the_bulk(self):
        text = self.digest()
        self.assertIn("fix the seed script", text)
        self.assertIn("Looking at the seeds now.", text)
        self.assertIn("→ Bash run the seeder", text)          # tool call collapsed to one line
        self.assertNotIn("SECRET-THOUGHT", text)              # thinking dropped
        self.assertNotIn("HUGE-TOOL-OUTPUT", text)            # tool results dropped
        self.assertNotIn("SUBAGENT-CHATTER", text)            # sidechains dropped
        self.assertNotIn("ignore me", text)                   # system-reminder stripped

    def test_carries_metadata_forward(self):
        text = self.digest()
        self.assertIn("cwd: /Users/x/proj", text)
        self.assertIn("gitBranch: main", text)

    def test_max_block_truncates(self):
        src = self.write_session("aaaa", extra=[
            {"type": "assistant", "cwd": "/Users/x/proj",
             "message": {"content": [{"type": "text", "text": "L" * 5000 + "TAIL"}]}}])
        self.shared.mkdir(parents=True, exist_ok=True)
        (self.shared / src.name).write_bytes(src.read_bytes())
        self.run_script(CONSUME, "digest", "aaaa", "--max-block", "100")
        self.assertNotIn("TAIL", (self.shared / "aaaa.digest.md").read_text())


class TestResumeAndDelete(Base):
    """The consuming profile is a DIFFERENT config dir from the publishing one —
    that separation is the whole point, so the fixture has to model it."""

    def setUp(self):
        super().setUp()
        self.env["CLAUDE_CONFIG_DIR"] = str(self.home / ".claude-work")

    def publish(self, sid="aaaa"):
        src = self.write_session(sid, nonce="N1")
        self.shared.mkdir(parents=True, exist_ok=True)
        dest = self.shared / src.name
        dest.write_bytes(src.read_bytes())
        return dest

    def test_resume_installs_under_the_cwd_slug(self):
        self.publish()
        r = self.run_script(CONSUME, "resume", "aaaa")
        installed = self.home / ".claude-work" / "projects" / "-Users-x-proj" / "aaaa.jsonl"
        self.assertTrue((self.home / ".claude" / "projects" / "-Users-x-proj" / "aaaa.jsonl").exists(),
                        "publishing profile's own transcript must survive")
        self.assertTrue(installed.exists())
        self.assertIn("claude --resume aaaa", r.stdout)

    def test_resume_refuses_to_clobber_without_force(self):
        self.publish()
        self.run_script(CONSUME, "resume", "aaaa")
        self.run_script(CONSUME, "resume", "aaaa", expect=1)
        self.run_script(CONSUME, "resume", "aaaa", "--force")

    def test_delete_removes_published_copy_and_digest(self):
        pub = self.publish()
        (self.shared / "aaaa.digest.md").write_text("x")
        self.run_script(CONSUME, "delete", "aaaa")
        self.assertFalse(pub.exists())
        self.assertFalse((self.shared / "aaaa.digest.md").exists())

    def test_delete_refuses_files_outside_the_shared_dir(self):
        src = self.write_session("aaaa")
        self.run_script(CONSUME, "delete", str(src), expect=1)
        self.assertTrue(src.exists(), "delete escaped the shared directory")


class TestSidecar(Base):
    """A session is the .jsonl plus a same-named directory of subagent transcripts
    and oversized tool results. Publishing only the .jsonl loses those silently,
    and a `claude --resume` of the copy then replays a session with holes in it."""

    def write_sidecar(self, sid):
        d = self.home / ".claude" / "projects" / "-Users-x-proj" / sid
        (d / "subagents").mkdir(parents=True, exist_ok=True)
        (d / "subagents" / "agent-1.jsonl").write_text('{"type":"assistant"}\n')
        (d / "tool-results").mkdir(parents=True, exist_ok=True)
        (d / "tool-results" / "big.txt").write_text("X" * 5000)
        return d

    def test_publish_carries_the_sidecar(self):
        self.write_session("aaaa", nonce="N1")
        self.write_sidecar("aaaa")
        r = self.run_script(PUBLISH, "--nonce", "N1")
        self.assertTrue((self.shared / "aaaa" / "subagents" / "agent-1.jsonl").exists())
        self.assertTrue((self.shared / "aaaa" / "tool-results" / "big.txt").exists())
        self.assertIn("sidecar", r.stdout)

    def test_publish_without_a_sidecar_still_works(self):
        self.write_session("aaaa", nonce="N1")
        r = self.run_script(PUBLISH, "--nonce", "N1")
        self.assertTrue((self.shared / "aaaa.jsonl").exists())
        self.assertNotIn("sidecar", r.stdout)

    def test_resume_installs_the_sidecar_into_the_consuming_profile(self):
        self.write_session("aaaa", nonce="N1")
        self.write_sidecar("aaaa")
        self.run_script(PUBLISH, "--nonce", "N1")
        self.env["CLAUDE_CONFIG_DIR"] = str(self.home / ".claude-work")
        self.run_script(CONSUME, "resume", "aaaa")
        installed = self.home / ".claude-work" / "projects" / "-Users-x-proj" / "aaaa"
        self.assertTrue((installed / "subagents" / "agent-1.jsonl").exists())
        self.assertTrue((installed / "tool-results" / "big.txt").exists())

    def test_delete_removes_the_sidecar_too(self):
        self.write_session("aaaa", nonce="N1")
        self.write_sidecar("aaaa")
        self.run_script(PUBLISH, "--nonce", "N1")
        self.run_script(CONSUME, "delete", "aaaa")
        self.assertFalse((self.shared / "aaaa").exists(), "sidecar left behind after delete")
        self.assertTrue((self.home / ".claude" / "projects" / "-Users-x-proj" / "aaaa").is_dir(),
                        "delete reached back into the publishing profile")


class TestRealProfilesUntouched(unittest.TestCase):
    def test_default_shared_dir_is_not_a_config_dir(self):
        pub = load(PUBLISH, "pub")
        con = load(CONSUME, "con")
        self.assertEqual(pub.DEFAULT_SHARED, con.DEFAULT_SHARED)
        self.assertNotIn(".claude", pub.DEFAULT_SHARED.parts[-2:])


if __name__ == "__main__":
    unittest.main()
