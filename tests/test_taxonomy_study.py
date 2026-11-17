import unittest

from lily.memory.db import Database
from lily.memory.taxonomy import store
from lily.memory.taxonomy.service import Taxonomy
from lily.memory.taxonomy.tree import Tree, load_config

BRANCHES = ("history science math philosophy culture language religion-belief arts-literature social-studies "
            "political-studies economics medicine technology education research-discovery").split()
KEPT = ("science/physics science/chemistry science/biology science/astronomy science/earth math/arithmetic "
        "math/algebra math/geometry math/trigonometry math/calculus math/statistics math/linear-algebra "
        "history/era history/event history/civilization history/institution").split()


class StudyAreaTests(unittest.TestCase):
    def setUp(self):
        self.tree = Tree(load_config())

    def test_every_study_branch_has_its_own_areas(self):
        for branch in BRANCHES:
            self.assertTrue(self.tree.children(f"study/{branch}"), branch)

    def test_ids_the_older_word_lists_already_use_are_defined_and_kept(self):
        for path in KEPT:
            self.assertIn("study/" + path, self.tree.nodes)

    def test_the_bridge_files_into_defined_areas_without_making_new_nodes(self):
        db = Database(":memory:")
        tax = Taxonomy(lambda: db)
        tax.classify("run", "1", "study/science/physics", source="auto:legacy", create=True)
        self.assertEqual(store.nodes(db), [])
        self.assertEqual(tax.refs(["study/science"]), [("run", "1")])

    def test_areas_stay_one_level_under_their_branch(self):
        areas = [path for path in self.tree.nodes if path.count("/") == 2]
        self.assertTrue(all(path.split("/")[1] in BRANCHES for path in areas))
        self.assertGreaterEqual(len(areas), 90)


if __name__ == "__main__":
    unittest.main()
