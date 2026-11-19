import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lily.tools import policy
from lily.tools.builtin import read_file, shell, write_file
from lily.utils.errors import ToolError
from lily.utils.paths import workplace


class WorkplaceTests(unittest.TestCase):
    def setUp(self):
        base = tempfile.mkdtemp()
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": base})
        patch.start()
        self.addCleanup(patch.stop)
        self.base = Path(base).resolve()
        self.write = write_file.Tool(None)

    def test_folder_is_created_where_the_user_pointed(self):
        self.assertEqual(workplace(), self.base / "Terminal_Lily_Workplace")
        self.assertTrue(workplace().is_dir())

    def test_relative_paths_start_in_the_workplace(self):
        self.write.execute({"path": "proj/a.txt", "content": "hi"})
        self.assertEqual((workplace() / "proj" / "a.txt").read_text(), "hi")
        self.assertEqual(read_file.Tool(None).execute({"path": "proj/a.txt"}), "hi")

    def test_writing_outside_is_refused(self):
        outside = self.base / "elsewhere.txt"
        for path in (str(outside), "../elsewhere.txt"):
            with self.assertRaisesRegex(ToolError, "outside the workplace"):
                self.write.execute({"path": path, "content": "x"})
        self.assertFalse(outside.exists())

    def test_shell_runs_inside_the_workplace(self):
        out = shell.Tool(None).execute({"command": "pwd"})
        self.assertEqual(out, f"exit code 0\n{workplace()}")

    def test_write_approval_asks_about_the_workplace_folder(self):
        self.assertEqual(policy.folder({"path": "proj/a.txt"}), workplace() / "proj")


if __name__ == "__main__":
    unittest.main()
