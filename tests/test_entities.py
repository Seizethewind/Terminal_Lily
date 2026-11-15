import tempfile
import tomllib
import unittest
from pathlib import Path

from lily.memory.entities import CLASSES, PATH, Taxonomy, label, name
from lily.memory.entity_find import build, find
from lily.utils.errors import ConfigError, LilyError

TAX = Taxonomy()
PATTERN = build(TAX.words)


class LabelTests(unittest.TestCase):
    def test_labels_are_tidied(self):
        self.assertEqual(label("Entity/Animal"), ("entity", "animal"))
        self.assertEqual(label("object"), ("object", "other"))
        self.assertEqual(label("location/water body"), ("location", "water body"))

    def test_bad_labels_are_refused(self):
        for bad in ("thing/x", "object/1", "object/a/b!", ""):
            with self.assertRaises(LilyError, msg=bad):
                label(bad)

    def test_names(self):
        self.assertEqual(name("  New   YORK "), "new york")
        for bad in ("", "a", "x" * 41, "no!"):
            with self.assertRaises(LilyError, msg=bad):
                name(bad)


class TaxonomyTests(unittest.TestCase):
    def test_the_shipped_list_has_all_three_classes_and_no_clashes(self):
        data = tomllib.loads(PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(data), set(CLASSES))
        listed = [w.lower() for subs in data.values() for words in subs.values() for w in words]
        self.assertEqual(len(listed), len(set(listed)), "a word is listed twice")
        for cls in CLASSES:
            self.assertGreaterEqual(len(data[cls]), 4, cls)

    def test_words_know_their_place(self):
        self.assertEqual(TAX.words["dog"], ("entity", "animal"))
        self.assertEqual(TAX.words["manila"], ("location", "city"))
        self.assertEqual(TAX.words["phone"], ("object", "device"))

    def test_your_own_words_win_and_describe_counts_them(self):
        tax = Taxonomy(extra=[("dog", "object", "toy"), ("xyzzy", "object", "thing")])
        self.assertEqual(tax.words["dog"], ("object", "toy"))
        self.assertIn("thing (1)", tax.describe())
        self.assertTrue(TAX.describe().startswith("entity"))

    def test_missing_file_is_empty_and_bad_toml_is_a_config_error(self):
        self.assertEqual(Taxonomy(Path("/nonexistent/x.toml")).words, {})
        bad = Path(tempfile.mkdtemp()) / "entities.toml"
        bad.write_text("[entity\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            Taxonomy(bad)


class FindTests(unittest.TestCase):
    def test_counts_words_and_plurals_ignoring_case(self):
        found = find(PATTERN, "My Dog met two dogs and a cat in Manila.")
        self.assertEqual(found, {"dog": 2, "cat": 1, "manila": 1})

    def test_longest_phrase_wins_and_parts_of_words_do_not_match(self):
        self.assertEqual(find(PATTERN, "I flew to New York"), {"new york": 1})
        self.assertEqual(find(PATTERN, "the catalog and a bushel"), {})

    def test_code_is_ignored(self):
        text = "use `mouse` here\n```python\nkey = dog\n```\nbut a real cat"
        self.assertEqual(find(PATTERN, text), {"cat": 1})

    def test_empty_inputs(self):
        self.assertEqual(find(PATTERN, None), {})
        self.assertEqual(find(None, "dog"), {})
        self.assertIsNone(build({}))


if __name__ == "__main__":
    unittest.main()
