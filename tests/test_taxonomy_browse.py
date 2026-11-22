import unittest

from lily.memory.db import Database
from lily.memory.taxonomy import browse, store
from lily.memory.taxonomy.tree import Tree, load_config
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply
from tests.memory_helpers import setup


class BrowseTests(unittest.TestCase):
    def setUp(self):
        self.tree, self.db = Tree(load_config()), Database(":memory:")

    def test_about_shows_the_meaning_and_what_is_inside(self):
        text = browse.about(self.tree, self.db, "study/science/physics")
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("study/science/physics  - Matter, energy"))
        self.assertTrue(any(line.startswith("  optics  - Light, lenses") for line in lines))
        self.assertEqual(len(lines), 1 + len(self.tree.children("study/science/physics")))

    def test_about_shows_counts_older_ids_and_empty_branches(self):
        store.label(self.db, "run", "1", "study/science/physics/optics", "user")
        self.assertIn("optics  1 record(s)", browse.about(self.tree, self.db, "study/science/physics"))
        self.assertIn("older ids: nature/animal", browse.about(self.tree, self.db, "nature/animal"))
        self.assertIn("(nothing inside yet)", browse.about(self.tree, self.db, "study/science/physics/relativity"))
        with self.assertRaisesRegex(LilyError, "not in the taxonomy"):
            browse.about(self.tree, self.db, "study/nothing")

    def test_find_lists_names_first_then_definitions(self):
        lines = browse.find(self.tree, "optics").splitlines()
        self.assertTrue(lines[0].startswith("study/science/physics/optics  - "))
        self.assertIn("nothing in the taxonomy mentions", browse.find(self.tree, "zzzz"))
        self.assertIn("more. Try a more exact word", browse.find(self.tree, "the"))
        with self.assertRaises(LilyError):
            browse.find(self.tree, "a")


class CommandTests(unittest.TestCase):
    def test_the_commands_are_wired_in(self):
        lily, _ = setup(text_reply("ok"))
        self.assertIn("optics", commands.run(lily, "/taxonomy about study/science/physics"))
        self.assertTrue(commands.run(lily, "/taxonomy find lenses").startswith("study/science/physics/optics"))
        self.assertIn("/taxonomy find <word>", commands.run(lily, "/taxonomy nonsense"))


if __name__ == "__main__":
    unittest.main()
