"""Tests for the code map: symbols, skipped folders and secrets, find, budget and the tool."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lily.tools import symbols
from lily.tools.builtin import code_map
from lily.utils.errors import ToolError
from lily.utils.paths import workplace


def build(root):
    (root / "app.py").write_text("class Box:\n    def open(self):\n        pass\n\ndef main():\n    pass\n")
    (root / "web").mkdir()
    (root / "web" / "ui.js").write_text("export function render() {}\nclass Panel {}\n")
    (root / "README.md").write_text("# Title\ntext\n## Usage\n")
    (root / "broken.py").write_text("def good():\n    pass\ndef (:\n")
    for skipped, name, text in (
        ("node_modules", "x.js", "function hidden() {}"),
        (".hidden", "h.py", "def stashed(): pass"),
    ):
        (root / skipped).mkdir()
        (root / skipped / name).write_text(text)
    (root / "token_notes.py").write_text("def leaky(): pass")


class MapTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        build(self.dir)

    def test_lists_classes_methods_functions_and_headings(self):
        text = symbols.build_map(self.dir)
        for wanted in ("class Box", "Box.open", "def main", "function render", "class Panel", "# Title", "## Usage"):
            self.assertIn(wanted, text)

    def test_a_python_file_with_a_syntax_error_still_gets_a_map(self):
        self.assertIn("def good", symbols.build_map(self.dir))

    def test_skips_dependency_folders_hidden_folders_and_secret_looking_files(self):
        text = symbols.build_map(self.dir)
        for unwanted in ("hidden", "stashed", "leaky"):
            self.assertNotIn(unwanted, text)

    def test_find_keeps_only_matches(self):
        text = symbols.build_map(self.dir, "render")
        self.assertIn("ui.js", text)
        self.assertNotIn("Box", text)
        self.assertIn("No source files", symbols.build_map(self.dir, "zzzz"))

    def test_a_small_budget_says_what_was_left_out(self):
        self.assertIn("not shown", symbols.build_map(self.dir, budget=10))


class ToolTests(unittest.TestCase):
    def test_the_tool_maps_the_workplace_and_refuses_a_file(self):
        base = tempfile.mkdtemp()
        with mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": base}):
            (workplace() / "tool.py").write_text("def from_tool():\n    pass\n")
            self.assertIn("def from_tool", code_map.Tool(None).execute({}))
            with self.assertRaises(ToolError):
                code_map.Tool(None).execute({"path": "tool.py"})


if __name__ == "__main__":
    unittest.main()
