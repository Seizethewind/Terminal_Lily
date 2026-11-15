import tempfile
import unittest
from pathlib import Path

from lily.memory.code_extract import MAX_CODE, extract
from lily.memory.code_guess import guess
from lily.memory.languages import GROUPS, Languages, clean
from lily.utils.errors import ConfigError

LANGS = Languages()


def fence(tag, code="x = 1"):
    return f"text before\n```{tag}\n{code}\n```\nafter"


class LanguagesTests(unittest.TestCase):
    def test_aliases_resolve_to_one_name(self):
        for tag in ("py", "Python3", "{.python}", "language-python"):
            self.assertEqual(LANGS.resolve(tag)["language"], "python")
        self.assertEqual(LANGS.resolve("c++")["language"], "cpp")
        self.assertEqual(LANGS.resolve("c#")["language"], "csharp")

    def test_known_languages_carry_their_place_in_the_tree(self):
        info = LANGS.resolve("rust")
        self.assertEqual((info["group"], info["family"], info["known"]), ("programming", "systems", True))

    def test_unlisted_languages_are_still_kept(self):
        info = LANGS.resolve("Brainfuck")
        self.assertEqual(info, {"language": "brainfuck", "group": "unknown", "family": "", "known": False})

    def test_non_code_tags_are_ignored(self):
        self.assertIsNone(LANGS.resolve("text"))
        self.assertIsNone(LANGS.resolve("OUTPUT"))
        self.assertEqual(clean("weird tag!"), "")

    def test_the_shipped_list_is_consistent(self):
        self.assertTrue(len(LANGS.info) >= 40)
        self.assertTrue({group for group, _ in LANGS.info.values()} <= set(GROUPS))
        aliases = [a for a in LANGS.alias if a not in LANGS.info]
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertTrue(all(name not in LANGS.ignore for name in LANGS.info))

    def test_missing_file_is_an_empty_list_and_bad_toml_is_a_config_error(self):
        self.assertEqual(Languages(Path("/nonexistent/x.toml")).info, {})
        bad = Path(tempfile.mkdtemp()) / "languages.toml"
        bad.write_text("[languages\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            Languages(bad)


class ExtractTests(unittest.TestCase):
    def test_tagged_block(self):
        (block,) = extract(fence("python", "print(1)\nprint(2)"), LANGS, "answer")
        self.assertEqual((block["language"], block["lines"], block["guessed"]), ("python", 2, False))
        self.assertEqual((block["code"], block["source"]), ("print(1)\nprint(2)", "answer"))

    def test_several_blocks_and_info_strings(self):
        text = fence("js title=\"a.js\"", "let a = 1;") + fence("rs", "fn main() {}")
        self.assertEqual([b["language"] for b in extract(text, LANGS, "answer")], ["javascript", "rust"])

    def test_untagged_block_is_guessed(self):
        (block,) = extract(fence("", "def add(a, b):\n    return a + b"), LANGS, "answer")
        self.assertEqual((block["language"], block["guessed"], block["known"]), ("python", True, True))

    def test_untagged_block_nobody_can_guess_is_still_stored(self):
        (block,) = extract(fence("", "zzz qqq"), LANGS, "question")
        self.assertEqual((block["language"], block["group"], block["known"]), ("unknown", "unknown", False))

    def test_text_blocks_are_skipped_and_plain_text_has_none(self):
        self.assertEqual(extract(fence("text"), LANGS, "answer"), [])
        self.assertEqual(extract("no code here", LANGS, "answer"), [])
        self.assertEqual(extract(None, LANGS, "answer"), [])

    def test_huge_blocks_are_cut(self):
        (block,) = extract(fence("python", "x" * (MAX_CODE + 50)), LANGS, "answer")
        self.assertTrue(block["code"].endswith("[cut]"))


class GuessTests(unittest.TestCase):
    def test_common_languages(self):
        cases = {
            "#!/usr/bin/env python3\nprint(1)": "python", "<?php echo 1;": "php", '{"a": [1, 2]}': "json",
            "#include <stdio.h>\nint main(){}": "c", "#include <iostream>\nint main(){}": "cpp",
            "package main\nfunc main() {}": "go", "fn main() {\n    let mut x = 1;\n}": "rust",
            "SELECT id FROM users WHERE x = 1;": "sql", "$ pkg install git": "bash",
            "const a = 1;\nconsole.log(a)": "javascript", "<!DOCTYPE html><html></html>": "html",
            "public class A { public static void main(String[] a) {} }": "java",
        }
        for code, language in cases.items():
            self.assertEqual(guess(code), language, code)

    def test_nothing_matches(self):
        self.assertEqual(guess("hello there"), "")


if __name__ == "__main__":
    unittest.main()
