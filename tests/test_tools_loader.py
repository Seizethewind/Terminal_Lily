import tempfile
import unittest
from pathlib import Path

from lily.tools import loader

GOOD = '''
from lily.tools.base import BaseTool

class Tool(BaseTool):
    name = "{name}"
    description = "A test plugin"
    def run(self):
        return "ok"
'''
BUILTIN = {"shell", "read_file", "write_file", "web_search", "termux_api", "rag_search"}


def plugin_folder(files):
    folder = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (folder / name).write_text(text, encoding="utf-8")
    return folder


class LoaderTests(unittest.TestCase):
    def test_all_builtin_tools_load(self):
        tools, errors = loader.load_all(None, plugin_folder({}))
        self.assertEqual({t.name for t in tools}, BUILTIN)
        self.assertEqual(errors, [])

    def test_plugins_are_loaded_in_name_order(self):
        folder = plugin_folder({"b.py": GOOD.format(name="beta"), "a.py": GOOD.format(name="alpha")})
        tools, _ = loader.load_all(None, folder)
        self.assertEqual([t.name for t in tools][-2:], ["alpha", "beta"])

    def test_underscore_files_are_ignored(self):
        folder = plugin_folder({"_hidden.py": GOOD.format(name="hidden")})
        tools, errors = loader.load_all(None, folder)
        self.assertNotIn("hidden", [t.name for t in tools])
        self.assertEqual(errors, [])

    def test_a_broken_plugin_is_reported_and_others_still_load(self):
        folder = plugin_folder({
            "bad_syntax.py": "def (:\n",
            "no_tool.py": "x = 1\n",
            "wrong_base.py": "class Tool:\n    pass\n",
            "crashes.py": "raise RuntimeError('boom')\n",
            "fine.py": GOOD.format(name="fine"),
        })
        tools, errors = loader.load_all(None, folder)
        names = {t.name for t in tools}
        self.assertIn("fine", names)
        self.assertTrue(BUILTIN <= names)
        self.assertEqual(len(errors), 4)
        self.assertTrue(any("bad_syntax.py" in e for e in errors))
        self.assertTrue(any("boom" in e for e in errors))

    def test_missing_plugin_folder_is_fine(self):
        tools, errors = loader.load_all(None, Path("/nonexistent/plugins"))
        self.assertEqual(len(tools), len(BUILTIN))
        self.assertEqual(errors, [])

    def test_the_shipped_example_plugin_loads(self):
        tools, errors = loader.load_all(None)
        self.assertIn("current_time", [t.name for t in tools])
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
