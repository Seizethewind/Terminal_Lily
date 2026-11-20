"""Tests for the auto-debug loop: failed commands are counted, and a stopped attempt is undone."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.self.debug_guard import DebugGuard, DebugLimit
from lily.self.hive_mind import HiveMind
from lily.self.rollback import Rollback
from lily.self.snapshot import Snapshot
from lily.self.staging import Staging
from lily.self.sub_agent import SubAgent
from lily.tools.builtin import shell
from lily.utils.paths import workplace

REGISTRY = SimpleNamespace(get=lambda name: shell.Tool(None) if name == "shell" else None, schemas=lambda: [])


def fake_lily(staging=None):
    sub = SimpleNamespace(staging=staging, autonomy=SimpleNamespace(level="full"), registry=REGISTRY)
    return SimpleNamespace(router=SimpleNamespace(get=lambda name: sub))


def shell_call(command):
    args = json.dumps({"command": command})
    return {"choices": [{"message": {"tool_calls": [{"id": "c", "function": {"name": "shell", "arguments": args}}]}}]}


class DebugTests(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": self.base})
        patch.start()
        self.addCleanup(patch.stop)
        self.dir = workplace()

    def agent(self, replies):
        script = iter(replies)
        models = SimpleNamespace(tier=lambda role, task: "light", chat=lambda *a: SimpleNamespace(data=next(script)))
        limits = {"approval_wait": 1, "worker_steps": 10, "debug_tries": 3}
        self.kit = SimpleNamespace(models=models, hive=HiveMind(), cfg=SimpleNamespace(limits=limits))
        return SubAgent(fake_lily(), self.kit, 1, "coder", "fix it")

    def test_failures_in_a_row_are_counted_then_stop_the_attempt(self):
        guard = DebugGuard(3)
        self.assertIn("try 1 of 3", guard.after("exit code 1\nboom"))
        guard.after("exit code 0\nfine")
        self.assertIn("try 1 of 3", guard.after("exit code 2\nboom"))
        self.assertIn("try 2 of 3", guard.after("exit code 2\nboom"))
        with self.assertRaises(DebugLimit) as caught:
            guard.after("exit code 2\nthe last error line")
        self.assertIn("the last error line", str(caught.exception))
        self.assertIn("try 1 of 3", DebugGuard(3).error("timed out"))

    def test_snapshot_puts_the_workplace_back(self):
        (self.dir / "a.txt").write_text("one")
        (self.dir / "sub").mkdir()
        (self.dir / "sub" / "b.txt").write_text("two")
        snap = Snapshot(self.dir, 100, 10_000)
        (self.dir / "a.txt").write_text("changed")
        (self.dir / "sub" / "b.txt").unlink()
        (self.dir / "c.txt").write_text("new")
        self.assertEqual(snap.restore(), (1, 2))
        self.assertEqual((self.dir / "a.txt").read_text(), "one")
        self.assertEqual((self.dir / "sub" / "b.txt").read_text(), "two")
        self.assertFalse((self.dir / "c.txt").exists())
        snap.discard()
        big = Snapshot(self.dir, 1, 10_000)
        self.assertFalse(big.ok)
        self.assertIsNone(big.restore())

    def test_staged_files_go_back_to_how_they_were(self):
        staging = Staging(Path(self.base) / "stage")
        old, fresh = self.dir / "keep.txt", self.dir / "fresh.txt"
        staging.stage_write(old, "old")
        rollback = Rollback(fake_lily(staging), {})
        rollback.before_write(old)
        staging.stage_write(old, "new")
        rollback.before_write(fresh)
        staging.stage_write(fresh, "x")
        self.assertIn("un-staged 2", rollback.undo())
        self.assertEqual(staging.read(old), "old")
        self.assertFalse(staging.has(fresh))

    def test_a_worker_that_keeps_failing_is_stopped_and_undone(self):
        agent = self.agent([shell_call("touch made.txt")] + [shell_call("exit 1")] * 3)
        with self.assertRaises(DebugLimit):
            agent.run()
        self.assertFalse((self.dir / "made.txt").exists())
        trail = " ".join(self.kit.hive.trail(1))
        self.assertIn("command failed", trail)
        self.assertIn("attempt undone", trail)

    def test_a_worker_that_recovers_keeps_its_changes(self):
        done = {"choices": [{"message": {"content": "all good"}}]}
        agent = self.agent([shell_call("touch made.txt"), shell_call("exit 1"), shell_call("exit 0"), done])
        self.assertEqual(agent.run(), "all good")
        self.assertTrue((self.dir / "made.txt").exists())


if __name__ == "__main__":
    unittest.main()
