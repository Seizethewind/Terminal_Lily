import tempfile
import unittest
from pathlib import Path

from lily.memory.taxonomy import parts
from lily.utils.errors import ConfigError


def make(main, extra):
    root = Path(tempfile.mkdtemp())
    (root / "taxonomy.toml").write_text(main, encoding="utf-8")
    (root / "taxonomy.d").mkdir()
    for name, text in extra.items():
        (root / "taxonomy.d" / name).write_text(text, encoding="utf-8")
    return root / "taxonomy.toml"


class PartsTests(unittest.TestCase):
    def test_extra_files_add_to_the_sections_of_the_main_file(self):
        path = make('[roots]\na = "x"\n[sub]\n"a/b" = "one"\n', {"more.toml": '[sub]\n"a/c" = "two"\n'})
        data = parts.load(path)
        self.assertEqual(data["roots"], {"a": "x"})
        self.assertEqual(set(data["sub"]), {"a/b", "a/c"})

    def test_a_key_defined_twice_is_a_config_error(self):
        path = make('[sub]\n"a/b" = "one"\n', {"more.toml": '[sub]\n"a/b" = "two"\n'})
        with self.assertRaisesRegex(ConfigError, "already defined"):
            parts.load(path)

    def test_a_broken_extra_file_is_a_config_error_and_other_names_are_left_alone(self):
        with self.assertRaises(ConfigError):
            parts.load(make("", {"bad.toml": "[sub\n"}))
        other = Path(tempfile.mkdtemp()) / "other.toml"
        other.write_text('[sub]\n"a/b" = "one"\n', encoding="utf-8")
        self.assertEqual(set(parts.load(other)["sub"]), {"a/b"})

    def test_the_shipped_entertainment_file_is_merged(self):
        from lily.memory.taxonomy.tree import load_config
        self.assertIn("study/entertainment/anime", load_config()[1])


if __name__ == "__main__":
    unittest.main()
