import unittest

from lily.memory.db import Database
from lily.memory.taxonomy import store
from lily.memory.taxonomy.service import Taxonomy
from lily.memory.taxonomy.tree import Tree, load_config

BRANCHES = ("history science math philosophy culture language religion-belief arts-literature social-studies "
            "political-studies economics medicine technology education research-discovery").split()
THINGS = "entity geography nature".split()   # knowledge about things, places and nature
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
        self.assertTrue(all(path.split("/")[1] in BRANCHES + THINGS for path in areas))
        self.assertGreaterEqual(len(areas), 90)

    def test_every_area_has_topics_under_it_and_nothing_hangs_loose(self):
        areas = [path for path in self.tree.nodes if path.count("/") == 2 and self.tree.children(path)]
        topics = [path for path in self.tree.nodes if path.count("/") == 3]
        self.assertGreaterEqual(len(areas), 97)
        self.assertGreaterEqual(len(topics), 700)
        for path in topics:
            self.assertIn(path.rsplit("/", 1)[0], self.tree.nodes)
        for path in self.tree.nodes:
            if path.count("/") == 2 and path.split("/")[1] in BRANCHES + THINGS:
                self.assertTrue(self.tree.children(path), path)

    def test_a_record_filed_on_a_topic_is_found_from_every_level_above(self):
        db = Database(":memory:")
        tax = Taxonomy(lambda: db)
        tax.classify("run", "1", "study/science/physics/optics")
        for path in ("study", "study/science", "study/science/physics", "study/science/physics/optics"):
            self.assertEqual(tax.refs([path]), [("run", "1")], path)

    def test_entity_geography_and_nature_areas_have_topics_and_nothing_goes_deeper(self):
        for branch in THINGS:
            areas = self.tree.children(f"study/{branch}")
            self.assertGreaterEqual(len(areas), 10, branch)
            for area in areas:
                topics = self.tree.children(area)
                self.assertGreaterEqual(len(topics), 3, area)
                self.assertFalse(any(self.tree.children(topic) for topic in topics), area)


if __name__ == "__main__":
    unittest.main()
