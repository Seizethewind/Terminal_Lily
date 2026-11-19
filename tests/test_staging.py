"""Tests for staged writes: nothing is saved until apply, apply is undoable, workers cannot apply."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.self.staging import Staging
from lily.self.worker_tools import LILY_ONLY
from lily.tools import policy
from lily.tools.builtin import apply_changes, read_file, write_file
from lily.utils.errors import ToolError
from lily.utils.paths import workplace


class StagingTests(unittest.TestCase):
    def setUp(self):
        base = tempfile.mkdtemp()
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": base})
        patch.start()
        self.addCleanup(patch.stop)
        self.staging = Staging(Path(base) / "stagedata")
        self.answer = True
        sub = SimpleNamespace(staging=self.staging)
        self.lily = SimpleNamespace(router=SimpleNamespace(get=lambda name: sub), confirm=lambda q: self.answer)
        self.dir = workplace()

    def stage(self, name, text, append=False):
        return self.staging.stage_write(self.dir / name, text, append)

    def test_staging_does_not_touch_the_files(self):
        self.stage("notes.txt", "hello")
        self.assertFalse((self.dir / "notes.txt").exists())
        self.assertEqual(self.staging.read(self.dir / "notes.txt"), "hello")
        self.assertIn("new", self.staging.changes())

    def test_apply_writes_and_undo_restores(self):
        old = self.dir / "a.txt"
        old.write_text("one\n")
        self.stage("a.txt", "two\n")
        self.stage("sub/b.txt", "fresh")
        self.assertIn("2 file", self.staging.apply())
        self.assertEqual((old.read_text(), (self.dir / "sub" / "b.txt").read_text()), ("two\n", "fresh"))
        self.assertEqual(self.staging.count(), 0)
        self.staging.undo()
        self.assertEqual(old.read_text(), "one\n")
        self.assertFalse((self.dir / "sub" / "b.txt").exists())

    def test_undo_leaves_files_edited_after_apply(self):
        file = self.dir / "a.txt"
        file.write_text("one")
        self.stage("a.txt", "two")
        self.staging.apply()
        file.write_text("my own edit")
        self.assertIn("edited", self.staging.undo())
        self.assertEqual(file.read_text(), "my own edit")

    def test_failed_apply_changes_nothing_and_keeps_the_files_waiting(self):
        good, blocker = self.dir / "good.txt", self.dir / "blocker"
        good.write_text("old")
        blocker.write_text("i am a file")
        self.stage("good.txt", "new")
        self.stage("blocker/child.txt", "x")
        with self.assertRaises(ToolError):
            self.staging.apply()
        self.assertEqual(good.read_text(), "old")
        self.assertEqual(self.staging.count(), 2)

    def test_append_starts_from_the_file_and_discard_drops(self):
        (self.dir / "a.txt").write_text("a\n")
        self.stage("a.txt", "b\n", append=True)
        self.stage("c.txt", "c")
        self.assertEqual(self.staging.read(self.dir / "a.txt"), "a\nb\n")
        self.assertIn("Dropped 1", self.staging.discard("c.txt"))
        self.assertIn("Dropped 1", self.staging.discard())

    def test_survives_a_restart(self):
        self.stage("a.txt", "x")
        self.assertEqual(Staging(self.staging.store.file.parent).count(), 1)

    def test_tools_stage_read_back_and_ask_once_to_apply(self):
        write_file.Tool(self.lily).execute({"path": "n.txt", "content": "hi"})
        self.assertFalse((self.dir / "n.txt").exists())
        self.assertEqual(read_file.Tool(self.lily).execute({"path": "n.txt"}), "hi")
        self.answer = False
        with self.assertRaises(ToolError):
            apply_changes.Tool(self.lily).execute({})
        self.assertFalse((self.dir / "n.txt").exists())
        self.answer = True
        apply_changes.Tool(self.lily).execute({})
        self.assertEqual((self.dir / "n.txt").read_text(), "hi")

    def test_policy_and_workers(self):
        self.assertEqual(policy.decide("write_file", {"path": "a.txt"}, True), "allow")
        self.assertEqual(policy.decide("write_file", {"path": "a.txt"}), "write")
        self.assertEqual(policy.decide("write_file", {"path": ".env"}, True), "ask")
        self.assertEqual(policy.decide("apply_changes", {}), "allow")
        self.assertTrue({"apply_changes", "undo_apply", "discard_changes"} <= LILY_ONLY)


if __name__ == "__main__":
    unittest.main()
