import tempfile
import unittest
from pathlib import Path

from lily.tools.builtin import read_file, write_file
from lily.utils.errors import ToolError


class FileToolTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.write = write_file.Tool(None)
        self.read = read_file.Tool(None)

    def path(self, name):
        return str(self.folder / name)

    def test_write_then_read(self):
        message = self.write.execute({"path": self.path("a.txt"), "content": "héllo"})
        self.assertIn("wrote", message)
        self.assertEqual(self.read.execute({"path": self.path("a.txt")}), "héllo")

    def test_write_creates_missing_folders(self):
        target = self.path("x/y/z.txt")
        self.write.execute({"path": target, "content": "deep"})
        self.assertEqual(Path(target).read_text(encoding="utf-8"), "deep")

    def test_append_adds_to_the_end(self):
        target = self.path("log.txt")
        self.write.execute({"path": target, "content": "one\n"})
        message = self.write.execute({"path": target, "content": "two\n", "append": True})
        self.assertIn("appended to", message)
        self.assertEqual(Path(target).read_text(encoding="utf-8"), "one\ntwo\n")

    def test_read_with_offset_continues_a_long_file(self):
        Path(self.path("long.txt")).write_text("0123456789", encoding="utf-8")
        self.assertEqual(self.read.execute({"path": self.path("long.txt"), "offset": "4"}), "456789")

    def test_read_errors(self):
        with self.assertRaisesRegex(ToolError, "not a file"):
            self.read.execute({"path": self.path("missing.txt")})
        with self.assertRaisesRegex(ToolError, "not a file"):
            self.read.execute({"path": str(self.folder)})
        with self.assertRaises(ToolError):
            self.read.execute({"path": self.path("x"), "offset": "far"})

    def test_write_error_is_a_tool_error(self):
        blocker = self.path("blocker")
        Path(blocker).write_text("i am a file", encoding="utf-8")
        with self.assertRaisesRegex(ToolError, "cannot write"):
            self.write.execute({"path": blocker + "/child.txt", "content": "x"})

    def test_binary_bytes_do_not_crash_reading(self):
        Path(self.path("bin")).write_bytes(b"ok\xff\xfe")
        self.assertTrue(self.read.execute({"path": self.path("bin")}).startswith("ok"))


if __name__ == "__main__":
    unittest.main()
