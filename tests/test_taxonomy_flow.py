import unittest

from lily.memory.taxonomy.legacy import target
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply
from tests.memory_helpers import setup

CODE_REPLY = "Sure:\n```python\nprint('hi')\n```\n"


def run(lily, line):
    return commands.run(lily, line)


def labels(memory, ref="1"):
    return [path for path, _ in memory.taxonomy.db.rows(
        "SELECT path, source FROM taxonomy_labels WHERE kind = 'run' AND ref = ? ORDER BY path", (ref,))]


class BridgeTests(unittest.TestCase):
    def test_old_classes_map_to_the_new_tree(self):
        mapping = {"entity": "entity", "entity/animal": "nature/animal", "location": "geography"}
        self.assertEqual(target(mapping, "entity", "person"), "entity/person")
        self.assertEqual(target(mapping, "entity", "animal"), "nature/animal")
        self.assertEqual(target(mapping, "location", "Water Body"), "geography/water-body")
        self.assertEqual(target(mapping, "math", "algebra"), "unknown/math")


class MemoryFlowTests(unittest.TestCase):
    def test_every_turn_is_labelled_automatically_and_the_chat_is_untouched(self):
        lily, memory = setup(text_reply(CODE_REPLY))
        lily.handle("tell me about my dog in Manila")
        self.assertEqual(labels(memory), ["entity/animal", "geography/settlement", "study/programming"])
        before = memory.db.rows("SELECT * FROM runs")
        run(lily, "/taxonomy scan")
        run(lily, "/taxonomy unlabel run all 1")
        self.assertEqual(labels(memory), [])
        self.assertEqual(memory.db.rows("SELECT * FROM runs"), before)   # the original is preserved

    def test_a_chat_with_nothing_to_file_stays_unclassified(self):
        lily, memory = setup(text_reply("ok"), text_reply("ok"))
        lily.handle("hello")
        lily.handle("there")
        self.assertEqual(labels(memory, "1"), [])
        self.assertEqual(run(lily, "/taxonomy unclassified"), "1  hello\n2  there")
        self.assertIn("unclassified  run 2", run(lily, "/taxonomy"))

    def test_your_labels_survive_a_rescan_and_do_not_duplicate_the_automatic_ones(self):
        lily, memory = setup(text_reply("Dogs bark."))
        lily.handle("hi")
        run(lily, "/taxonomy label run study/history 1")
        run(lily, "/taxonomy label run nature/animal 1")   # the older id: it files under entity/animal
        run(lily, "/taxonomy scan")
        run(lily, "/taxonomy scan")
        self.assertEqual(labels(memory), ["entity/animal", "study/history"])
        self.assertIn("entity/animal  (user)", run(lily, "/taxonomy of run 1"))


class CommandTests(unittest.TestCase):
    def test_build_label_and_filter_from_the_command_line(self):
        lily, _ = setup(text_reply("Dogs bark."))
        lily.handle("hi")
        self.assertEqual(run(lily, "/taxonomy add study/history/medieval the middle ages"),
                         "added study/history/medieval")
        run(lily, "/taxonomy label run study/history/medieval 1")
        self.assertEqual(run(lily, "/taxonomy show study"), "run 1")
        self.assertEqual(run(lily, "/taxonomy show all study entity"), "run 1")
        self.assertEqual(run(lily, "/taxonomy show geography"), "nothing filed there")
        tree = run(lily, "/taxonomy")
        self.assertIn("study  1 record(s)  - Knowledge", tree)
        self.assertIn("    medieval  1 record(s)  - the middle ages", tree)
        self.assertIn("entity  1 record(s)", tree)

    def test_mistakes_are_explained_not_raised_as_crashes(self):
        lily, _ = setup(text_reply("ok"))
        self.assertIn("Usage", run(lily, "/taxonomy nonsense"))
        self.assertIn("Usage", run(lily, "/taxonomy label run study"))
        with self.assertRaisesRegex(LilyError, "only categories you added"):
            run(lily, "/taxonomy remove study/none")   # the UI loop shows this as a plain message


class NotesTests(unittest.TestCase):
    def test_notes_can_be_filed_and_searched_by_category(self):
        lily, memory = setup(text_reply("ok"))
        rag = lily.router.get("rag")
        folder = lily.settings.data_dir / "notes"
        folder.mkdir()
        (folder / "pets.md").write_text("The cat is called Mochi.", encoding="utf-8")
        (folder / "trip.md").write_text("The cat rode a ferry to Cebu.", encoding="utf-8")
        rag.ingest(folder)
        pets, trip = sorted(source for source, _ in rag.store.sources())
        self.assertEqual(run(lily, "/taxonomy unclassified note").count("\n"), 1)
        run(lily, "/taxonomy add geography/trips")
        run(lily, f"/taxonomy label note geography/trips {trip}")
        self.assertEqual(run(lily, "/taxonomy unclassified note"), pets)
        found = run(lily, "/taxonomy search geography cat")
        self.assertIn("ferry", found)
        self.assertNotIn("Mochi", found)
        self.assertEqual(len(rag.search("cat")), 2)   # unfiltered search is unchanged
        self.assertEqual(rag.search("cat", sources=set()), [])
        self.assertIn("no matching notes", run(lily, "/taxonomy search geography zebra"))


if __name__ == "__main__":
    unittest.main()
