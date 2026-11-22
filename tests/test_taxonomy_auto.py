import tempfile
import unittest
from pathlib import Path

from lily.memory import run_log
from lily.memory.db import Database
from lily.memory.taxonomy.autolabel import Matcher, load_settings
from lily.memory.taxonomy.service import Taxonomy
from lily.memory.taxonomy.tree import Tree, load_config
from lily.utils.errors import ConfigError
from tests.fakes import text_reply
from tests.memory_helpers import setup

ROOTS = {"entity": "e", "geography": "g", "nature": "n", "study": "s"}
SUBS = {"study/science": "science", "study/science/physics": "matter and energy",
        "study/science/physics/optics": "light and lenses", "study/science/physics/mechanics": "motion and force",
        "study/science/biology": "life", "study/science/biology/model": "a word too common to match",
        "study/geography": "places", "study/geography/gis-remote-sensing": "mapping with computers"}
AUTO = ({"model"}, {"gis": "study/geography/gis-remote-sensing", "nowhere": "study/none"}, 3)


def make(auto=AUTO):
    db = Database(":memory:")
    return db, Taxonomy(lambda: db, config=(ROOTS, SUBS, {}), auto=auto)


def chat(db, tax, user, answer="ok"):
    run = run_log.record(db, {"user_text": user, "answer": answer})
    tax.index_run(run, user, answer)
    return str(run)


def labels(tax, run):
    return tax.of("run", run).splitlines()


class MatcherTests(unittest.TestCase):
    def setUp(self):
        self.matcher = Matcher(Tree((ROOTS, SUBS, {})), AUTO)

    def test_a_name_in_your_message_is_enough_but_in_her_answer_it_takes_two(self):
        self.assertEqual(self.matcher.paths("how do lenses and optics work?", ""), ["study/science/physics/optics"])
        self.assertEqual(self.matcher.paths("hi", "Optics is fun."), [])
        self.assertEqual(self.matcher.paths("hi", "Optics is fun. Optics again."), ["study/science/physics/optics"])

    def test_plurals_and_extra_words_match_and_bad_extra_words_are_ignored(self):
        self.assertEqual(self.matcher.paths("a gis course", ""), ["study/geography/gis-remote-sensing"])
        self.assertEqual(self.matcher.paths("nowhere", ""), [])   # an extra word pointing at nothing is ignored
        self.assertEqual(self.matcher.paths("MECHANICS", ""), ["study/science/physics/mechanics"])

    def test_common_names_code_and_broad_branches_are_ignored(self):
        for text in ("my model is fine", "the science of places", "`optics` and\n```\nmechanics\n```"):
            self.assertEqual(self.matcher.paths(text, ""), [], text)

    def test_the_most_talked_about_come_first_and_the_list_is_capped(self):
        paths = self.matcher.paths("optics optics mechanics gis optics gis", "")
        self.assertEqual(paths, ["study/science/physics/optics", "study/geography/gis-remote-sensing",
                                 "study/science/physics/mechanics"])
        self.assertEqual(len(Matcher(Tree((ROOTS, SUBS, {})), (set(), {}, 1)).paths("optics mechanics", "")), 1)


class LabellingTests(unittest.TestCase):
    def test_a_chat_is_filed_automatically_and_your_labels_are_kept(self):
        db, tax = make()
        run = chat(db, tax, "explain optics")
        tax.classify("run", run, "study/science/physics/mechanics")
        tax.scan()
        tax.scan()
        self.assertEqual(labels(tax, run), ["study/science/physics/mechanics  (user)",
                                            "study/science/physics/optics  (auto:tree)"])

    def test_your_label_on_the_same_path_wins_and_survives_a_rescan(self):
        db, tax = make()
        run = chat(db, tax, "explain optics")
        tax.classify("run", run, "study/science/physics/optics")
        tax.scan()
        self.assertEqual(labels(tax, run), ["study/science/physics/optics  (user)"])

    def test_a_rescan_drops_automatic_labels_that_no_longer_apply(self):
        db, tax = make()
        run = chat(db, tax, "explain optics")
        tax.auto = ({"optics"}, {}, 3)   # the name is now on the skip list
        self.assertIn("made 0 automatic", tax.scan())
        self.assertEqual(tax.of("run", run), "no labels: it is unclassified")

    def test_end_to_end_with_the_shipped_config(self):
        lily, memory = setup(text_reply("Light bends through lenses."))
        lily.handle("tell me about optics and genetics")
        paths = [path for path, _ in memory.taxonomy.db.rows("SELECT path, source FROM taxonomy_labels")]
        self.assertEqual(paths, ["study/science/biology/genetics", "study/science/physics/optics"])


class SettingsTests(unittest.TestCase):
    def test_the_shipped_settings_load_and_point_at_real_categories(self):
        skip, words, limit = load_settings()
        tree = Tree(load_config())
        self.assertTrue(skip and 1 <= limit <= 20)
        self.assertTrue(all(path in tree.nodes for path in words.values()))

    def test_bad_settings_are_a_config_error(self):
        path = Path(tempfile.mkdtemp()) / "taxonomy_auto.toml"
        path.write_text("max_labels = 0\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_settings(path)


if __name__ == "__main__":
    unittest.main()
