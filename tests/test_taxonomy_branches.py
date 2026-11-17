import unittest

from lily.memory.db import Database
from lily.memory.taxonomy import store
from lily.memory.taxonomy.service import Taxonomy
from lily.memory.taxonomy.tree import Tree, load_config
from lily.utils.errors import ConfigError

SECOND_LEVEL = {
    "entity": "living non-living person animal plant microorganism object material organization group",
    "geography": "continent country-territory administrative-region settlement landform water-body "
                 "geographic-feature location boundary spatial-relationship",
    "nature": "ecosystem habitat climate weather natural-phenomenon natural-process geological-system "
              "natural-resource environmental-condition biodiversity",
    "study": "history science math philosophy culture language religion-belief arts-literature social-studies "
             "political-studies economics medicine technology education research-discovery",
}
ROOTS = {"entity": "e", "geography": "g", "nature": "n", "study": "s"}
SUBS = {"entity/animal": "a", "study/technology": "t", "study/arts-literature": "l"}


def make(alias=None, inside=None):
    db = Database(":memory:")
    config = (ROOTS, SUBS, {}, alias or {"nature/animal": "entity/animal"},
              inside or {"study/computing": "study/technology"})
    return db, Taxonomy(lambda: db, config=config)


class ShippedConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.tree = Tree(self.config)

    def test_the_four_top_level_categories_are_unchanged(self):
        self.assertEqual(self.config[0], {
            "entity": "Things that exist", "geography": "Places and spatial information",
            "nature": "Natural systems and phenomena",
            "study": "Knowledge, disciplines, discoveries, history, concepts and research"})

    def test_every_broad_branch_is_there(self):
        for root, names in SECOND_LEVEL.items():
            self.assertEqual({path.split("/")[1] for path in self.tree.nodes if path.startswith(root + "/")},
                             set(names.split()), root)

    def test_every_branch_has_its_own_definition(self):
        texts = [text for path, text in self.tree.nodes.items() if "/" in path]
        self.assertTrue(all(len(text) > 20 for text in texts))
        self.assertEqual(len(texts), len(set(texts)))

    def test_only_study_goes_below_the_second_level_and_nothing_passes_the_fourth(self):
        self.assertTrue(all(path.count("/") <= 3 for path in self.tree.nodes))
        self.assertTrue(all(path.startswith("study/") for path in self.tree.nodes if path.count("/") >= 2))

    def test_the_bridge_and_older_ids_point_at_real_places(self):
        for target in self.tree.legacy.values():
            self.assertIn(target.split("/")[0], self.tree.roots)
        for new in self.tree.moved.values():
            self.assertIn(new, self.tree.nodes)
        self.assertIn("entity/animal", self.tree.alias.values())

    def test_bad_older_ids_are_config_errors(self):
        for alias in ({"nature/x": "entity/missing"}, {"entity/animal": "entity/person"}, {"nature/x": "nature/y"}):
            with self.assertRaises(ConfigError, msg=alias):
                Tree((ROOTS, SUBS, {}, alias, {}))


class OlderIdTests(unittest.TestCase):
    def test_old_labels_are_found_under_the_new_branch_and_not_under_their_old_parent(self):
        db, tax = make()
        store.label(db, "run", "1", "nature/animal", "user")   # filed before the change
        store.label(db, "run", "2", "entity/animal", "user")
        self.assertEqual(tax.refs(["entity/animal"]), [("run", "1"), ("run", "2")])
        self.assertEqual(tax.refs(["nature/animal"]), [("run", "1"), ("run", "2")])
        self.assertEqual(tax.refs(["entity"]), [("run", "1"), ("run", "2")])
        self.assertEqual(tax.refs(["nature"]), [])
        self.assertEqual(db.rows("SELECT path FROM taxonomy_labels WHERE ref = '1'"), [("nature/animal",)])

    def test_new_labels_use_the_new_id_and_unlabel_clears_both(self):
        db, tax = make()
        tax.classify("run", "1", "nature/animal")
        store.label(db, "run", "1", "nature/animal", "user")
        self.assertEqual(tax.of("run", "1"), "entity/animal  (user)\nnature/animal  (user)")
        self.assertEqual(tax.unclassify("run", "1", "entity/animal"), "removed 2 label(s)")

    def test_a_branch_nested_inside_a_broader_one_counts_toward_it(self):
        db, tax = make()
        store.label(db, "run", "1", "study/computing", "user")
        tax.add("study/technology/robots")
        tax.classify("run", "2", "study/technology/robots")
        self.assertEqual(tax.refs(["study/technology"]), [("run", "1"), ("run", "2")])
        self.assertEqual(tax.refs(["study/computing"]), [("run", "1")])
        self.assertIn("  technology  2 record(s)", tax.report())

    def test_the_report_folds_renamed_ids_and_nests_the_others(self):
        db, tax = make()
        store.label(db, "run", "1", "nature/animal", "user")
        store.label(db, "run", "2", "study/computing", "user")
        store.add_node(db, "study/computing")   # made by the bridge the first time a chat used it
        lines = tax.report().splitlines()
        self.assertTrue(any(line.startswith("entity  1 record(s)") for line in lines))
        self.assertIn("    computing  1 record(s)", lines)
        self.assertFalse(any("not in the tree" in line or line.strip().startswith("animal") and "nature" in line
                             for line in lines))

    def test_an_older_id_cannot_be_added_again(self):
        _, tax = make()
        with self.assertRaisesRegex(Exception, "older id of 'entity/animal'"):
            tax.add("nature/animal")


if __name__ == "__main__":
    unittest.main()
