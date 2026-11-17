import tempfile
import unittest
from pathlib import Path

from lily.memory.taxonomy.paths import MAX_DEPTH, ancestors, clean, is_unknown, parent, slug
from lily.memory.taxonomy.tree import Tree, load_config
from lily.utils.errors import ConfigError, LilyError

ROOTS = {"entity": "e", "geography": "g", "nature": "n", "study": "s"}


def toml(text):
    path = Path(tempfile.mkdtemp()) / "taxonomy.toml"
    path.write_text(text, encoding="utf-8")
    return path


class PathTests(unittest.TestCase):
    def test_paths_are_tidied(self):
        self.assertEqual(clean("Study / History"), "study/history")
        self.assertEqual(clean("/study/Data Structure/"), "study/data-structure")
        self.assertEqual(slug("C++ Basics!"), "c-basics")

    def test_bad_paths_are_refused(self):
        for bad in ("", "/", "a//b", "../x", "!!!", "/".join(["a"] * (MAX_DEPTH + 1))):
            with self.assertRaises(LilyError, msg=bad):
                clean(bad)

    def test_helpers(self):
        self.assertEqual(parent("a/b/c"), "a/b")
        self.assertEqual(parent("a"), "")
        self.assertEqual(ancestors("a/b/c"), ["a", "a/b"])
        self.assertTrue(is_unknown("unknown") and is_unknown("unknown/x"))
        self.assertFalse(is_unknown("unknownish/x"))


class ConfigTests(unittest.TestCase):
    def test_the_shipped_file_has_the_four_top_level_categories(self):
        roots, subs, legacy, alias, inside = load_config()
        self.assertEqual(list(roots), ["entity", "geography", "nature", "study"])
        self.assertTrue(all(path.split("/")[0] in roots for path in legacy.values()))
        self.assertEqual(Tree((roots, subs, legacy, alias, inside)).roots, ("entity", "geography", "nature", "study"))

    def test_a_missing_file_is_an_empty_taxonomy(self):
        self.assertEqual(load_config(Path("/nonexistent/t.toml")), ({}, {}, {}, {}, {}))

    def test_bad_files_are_config_errors(self):
        for text in ("[roots\n", '[roots]\n"a/b" = "x"\n', '[roots]\nunknown = "x"\n', '[sub]\n"" = "x"\n'):
            with self.assertRaises(ConfigError, msg=text):
                load_config(toml(text))

    def test_children_may_be_listed_before_their_parent(self):
        config = ({"study": "s"}, {"study/a/b": "", "study/a": ""}, {})
        self.assertIn("study/a/b", Tree(config).nodes)

    def test_a_child_without_a_parent_is_a_config_error(self):
        with self.assertRaisesRegex(ConfigError, "needs 'study/a'"):
            Tree(({"study": "s"}, {"study/a/b": ""}, {}))


class TreeTests(unittest.TestCase):
    def setUp(self):
        self.tree = Tree((ROOTS, {"study/history": "h", "study/art": "a"}, {}))

    def test_walk_lists_roots_in_order_and_children_alphabetically(self):
        self.assertEqual(self.tree.walk(), [
            ("entity", 0), ("geography", 0), ("nature", 0), ("study", 0), ("study/art", 1), ("study/history", 1)])

    def test_runtime_additions_join_the_tree(self):
        tree = Tree((ROOTS, {}, {}), extra=[("nature/animal", "")])
        self.assertTrue(tree.has("nature/animal"))
        self.assertEqual(tree.children("nature"), ["nature/animal"])

    def test_has_accepts_unknown_paths_without_registration(self):
        self.assertTrue(self.tree.has("unknown") and self.tree.has("unknown/whatever"))
        self.assertFalse(self.tree.has("study/physics"))

    def test_check_new(self):
        self.assertEqual(self.tree.check_new("Study/Physics"), "study/physics")
        self.assertEqual(self.tree.check_new("study/history/medieval"), "study/history/medieval")
        for bad, why in (("physics", "top-level"), ("unknown/x", "top-level"), ("study/a/b", "does not exist"),
                         ("study/history", "already exists"), ("food/pizza", "does not exist")):
            with self.assertRaisesRegex(LilyError, why, msg=bad):
                self.tree.check_new(bad)


if __name__ == "__main__":
    unittest.main()
