import unittest

from lily.memory import run_log
from lily.memory.db import Database
from lily.memory.taxonomy.service import Taxonomy
from lily.utils.errors import LilyError

ROOTS = {"entity": "Things that exist", "geography": "Places", "nature": "Nature", "study": "Study"}
CONFIG = (ROOTS, {"study/history": "the past"}, {})


def make(notes=()):
    db = Database(":memory:")
    return db, Taxonomy(lambda: db, lambda: list(notes), config=CONFIG)


def chat(db, text="hello"):
    return str(run_log.record(db, {"user_text": text, "answer": "an answer"}))


class ClassifyTests(unittest.TestCase):
    def test_a_record_can_have_several_categories(self):
        db, tax = make()
        run = chat(db)
        tax.add("nature/animal")
        tax.classify("run", run, "study/history")
        tax.classify("run", run, "nature/animal")
        tax.classify("run", run, "study/history")   # again: no duplicate
        self.assertEqual(tax.of("run", run).splitlines(), ["nature/animal  (user)", "study/history  (user)"])

    def test_filtering_finds_records_in_a_category_and_below_it(self):
        db, tax = make()
        a, b = chat(db), chat(db)
        tax.add("study/history/medieval")
        tax.add("nature/animal")
        tax.classify("run", a, "study/history/medieval")
        tax.classify("run", b, "study/history")
        tax.classify("run", b, "nature/animal")
        self.assertEqual(tax.refs(["study/history"]), [("run", a), ("run", b)])
        self.assertEqual(tax.refs(["study/history/medieval"]), [("run", a)])
        self.assertEqual(tax.refs(["study", "nature"], mode="any"), [("run", a), ("run", b)])
        self.assertEqual(tax.refs(["study", "nature"], mode="all"), [("run", b)])
        self.assertEqual(tax.refs(["study"], kind="note"), [])
        with self.assertRaises(LilyError):
            tax.refs([])

    def test_a_path_that_is_not_in_the_tree_is_refused_with_a_hint(self):
        _, tax = make()
        with self.assertRaisesRegex(LilyError, "/taxonomy add study/physics"):
            tax.classify("run", "1", "study/physics")

    def test_create_registers_missing_levels_below_an_existing_top_level(self):
        db, tax = make()
        tax.classify("run", "1", "study/science/physics", create=True)
        self.assertEqual(tax.tree.children("study/science"), ["study/science/physics"])
        self.assertIn("study/science", Taxonomy(lambda: db, config=CONFIG).tree.nodes)   # kept in the database
        with self.assertRaisesRegex(LilyError, "top-level"):
            tax.classify("run", "1", "food/pizza", create=True)

    def test_unknown_is_a_holding_area_that_needs_no_registration(self):
        db, tax = make()
        tax.classify("run", chat(db), "unknown/odd-thing")
        self.assertEqual(tax.refs(["unknown"]), [("run", "1")])
        self.assertIn("unknown  1 record(s)", tax.report())

    def test_your_label_replaces_an_automatic_one_on_the_same_path(self):
        db, tax = make()
        tax.classify("run", "1", "study/history", source="auto:legacy")
        tax.classify("run", "1", "study/history")
        self.assertEqual(tax.of("run", "1"), "study/history  (user)")

    def test_bad_kinds_and_refs_are_refused(self):
        _, tax = make()
        for kind, ref in (("Bad Kind!", "1"), ("", "1"), ("run", ""), ("run", "x" * 301)):
            with self.assertRaises(LilyError, msg=(kind, ref)):
                tax.classify(kind, ref, "study/history")

    def test_unclassify(self):
        _, tax = make()
        tax.classify("run", "1", "study/history")
        tax.classify("run", "1", "unknown")
        self.assertEqual(tax.unclassify("run", "1", "unknown"), "removed 1 label(s)")
        self.assertEqual(tax.unclassify("run", "1"), "removed 1 label(s)")
        self.assertIn("unclassified", tax.of("run", "1"))


class GrowthTests(unittest.TestCase):
    def test_a_new_kind_of_record_needs_no_setup(self):
        _, tax = make()
        tax.classify("document", "report.pdf", "study/history")
        self.assertEqual(tax.refs(["study"]), [("document", "report.pdf")])

    def test_a_new_kind_can_be_listed_for_unclassified(self):
        _, tax = make()
        tax.kinds["document"] = lambda: [("a.pdf", "A"), ("b.pdf", "B")]
        tax.classify("document", "a.pdf", "study/history")
        self.assertEqual(tax.unclassified("document"), [("b.pdf", "B")])

    def test_remove_only_what_you_added_and_only_when_empty(self):
        _, tax = make()
        tax.add("study/art")
        tax.classify("run", "1", "study/art")
        with self.assertRaisesRegex(LilyError, "still has"):
            tax.remove("study/art")
        tax.unclassify("run", "1")
        self.assertEqual(tax.remove("study/art"), "removed study/art")
        with self.assertRaisesRegex(LilyError, "only categories you added"):
            tax.remove("study/history")


if __name__ == "__main__":
    unittest.main()
