"""Tests for the edit ladder: exact match, forgiving match, syntax guard and staged edits."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.self.staging import Staging
from lily.tools import edit_engine, syntax_check
from lily.tools.builtin import edit_file, write_file
from lily.utils.errors import ToolError
from lily.utils.paths import workplace

CODE = "def f():\n    x = 1\n    return x\n"


class EngineTests(unittest.TestCase):
    def test_exact_match_must_be_unique(self):
        self.assertEqual(edit_engine.apply_edit("a b c", "b", "X"), ("a X c", "exact"))
        with self.assertRaisesRegex(ToolError, "3 times"):
            edit_engine.apply_edit("a a a", "a", "b")
        with self.assertRaises(ToolError):
            edit_engine.apply_edit("abc", "", "x")

    def test_wrong_indentation_is_forgiven_and_fixed(self):
        result = edit_engine.apply_edit(CODE, "x = 1\nreturn x", "x = 2\nreturn x")
        self.assertEqual(result, ("def f():\n    x = 2\n    return x\n", "ignoring spaces"))

    def test_deleting_a_block_and_the_not_found_hint(self):
        text, _ = edit_engine.apply_edit("if x:\n    one()\n    two()\n", "one()\n  two()", "")
        self.assertEqual(text, "if x:\n")
        with self.assertRaisesRegex(ToolError, "closest line is 2"):
            edit_engine.apply_edit(CODE, "x = 100", "x")


class SyntaxTests(unittest.TestCase):
    def test_broken_results_are_refused_only_when_they_were_fine_before(self):
        self.assertIsNotNone(syntax_check.error("a.py", "def (:"))
        self.assertIsNone(syntax_check.error("a.txt", "def (:"))
        self.assertIsNotNone(syntax_check.breaks("a.py", "x = 1\n", "def (:"))
        self.assertIsNone(syntax_check.breaks("a.py", "def (:", "def (:!"))
        self.assertIsNotNone(syntax_check.breaks("a.json", None, "{bad"))
        self.assertIsNone(syntax_check.breaks("a.json", None, '{"ok": 1}'))


class ToolTests(unittest.TestCase):
    def setUp(self):
        base = tempfile.mkdtemp()
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": base})
        patch.start()
        self.addCleanup(patch.stop)
        self.dir, self.staging = workplace(), Staging(Path(base) / "stage")
        sub = SimpleNamespace(staging=self.staging)
        self.lily = SimpleNamespace(router=SimpleNamespace(get=lambda name: sub))

    def test_an_edit_of_a_staged_file_stays_staged(self):
        write_file.Tool(self.lily).execute({"path": "m.py", "content": CODE})
        edit_file.Tool(self.lily).execute({"path": "m.py", "old": "x = 1", "new": "x = 5"})
        self.assertIn("x = 5", self.staging.read(self.dir / "m.py"))
        self.assertFalse((self.dir / "m.py").exists())

    def test_an_edit_that_breaks_python_is_refused(self):
        write_file.Tool(self.lily).execute({"path": "m.py", "content": CODE})
        with self.assertRaisesRegex(ToolError, "break the file"):
            edit_file.Tool(self.lily).execute({"path": "m.py", "old": "return x", "new": "return ("})
        self.assertEqual(self.staging.read(self.dir / "m.py"), CODE)

    def test_without_staging_the_file_changes_and_a_missing_file_is_an_error(self):
        (self.dir / "n.txt").write_text("hello world")
        edit_file.Tool(None).execute({"path": "n.txt", "old": "world", "new": "there"})
        self.assertEqual((self.dir / "n.txt").read_text(), "hello there")
        with self.assertRaises(ToolError):
            edit_file.Tool(None).execute({"path": "nope.txt", "old": "a", "new": "b"})

    def test_write_file_refuses_a_broken_new_python_file_but_not_appends(self):
        with self.assertRaises(ToolError):
            write_file.Tool(None).execute({"path": "bad.py", "content": "def (:"})
        self.assertFalse((self.dir / "bad.py").exists())
        write_file.Tool(None).execute({"path": "ok.py", "content": "x = 1\n"})
        write_file.Tool(None).execute({"path": "ok.py", "content": "def (:", "append": True})
        self.assertIn("def (:", (self.dir / "ok.py").read_text())


if __name__ == "__main__":
    unittest.main()
