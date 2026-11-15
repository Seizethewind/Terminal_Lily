import unittest

from lily.ui import commands
from tests.fakes import text_reply
from tests.memory_helpers import setup


class EntityFlowTests(unittest.TestCase):
    def test_every_turn_is_filed_as_it_happens(self):
        lily, memory = setup(text_reply("Dogs are loyal."))
        lily.handle("tell me about Japan")
        rows = memory.db.rows("SELECT name, cls, sub FROM entity_mentions ORDER BY name")
        self.assertEqual(rows, [("dog", "entity", "animal"), ("japan", "location", "country")])

    def test_subjects_are_filed_next_to_the_things(self):
        lily, memory = setup(text_reply("Photosynthesis is biology."))
        lily.handle("explain the quadratic formula in a haiku about the Renaissance")
        rows = memory.db.rows("SELECT cls, sub, name FROM entity_mentions ORDER BY cls, name")
        self.assertEqual(rows, [
            ("history", "era", "renaissance"), ("literature", "form", "haiku"),
            ("math", "algebra", "quadratic"), ("science", "biology", "biology"),
            ("science", "biology", "photosynthesis")])
        report = commands.run(lily, "/entity").splitlines()
        self.assertEqual([x for x in report if not x.startswith(" ")], ["literature", "science", "math", "history"])
        self.assertIn("math", commands.run(lily, "/entity classes"))

    def test_computing_and_programming_are_filed_too(self):
        lily, memory = setup(text_reply("Use recursion, or a queue."))
        lily.handle("explain the binary search algorithm in python")
        rows = memory.db.rows("SELECT cls, sub, name FROM entity_mentions ORDER BY cls, name")
        self.assertEqual(rows, [
            ("computing", "algorithm", "algorithm"), ("computing", "algorithm", "binary search"),
            ("computing", "data structure", "queue"), ("programming", "language", "python"),
            ("programming", "concept", "recursion")])
        self.assertIn("1x queue  [data structure]", commands.run(lily, "/entity show computing/data structure"))
        self.assertIn("programming", commands.run(lily, "/entity classes"))

    def test_subclass_names_with_spaces_work_in_commands(self):
        lily, _ = setup(text_reply("ok"))
        self.assertIn("computing > data structure", commands.run(lily, "/entity add stack computing/data structure"))
        self.assertIn("math > linear algebra", commands.run(lily, "/entity add dot product math/linear algebra"))
        self.assertIn("added 'blue pen' as object > other", commands.run(lily, "/entity add blue pen object"))

    def test_slash_commands(self):
        lily, _ = setup(text_reply("A cat."))
        lily.handle("what is on my desk? phone?")
        self.assertIn("device: phone x1", commands.run(lily, "/entity"))
        self.assertIn("entity", commands.run(lily, "/entity classes"))
        self.assertIn("cat", commands.run(lily, "/entity show entity/animal"))
        self.assertIn("chat #1", commands.run(lily, "/entity find phone"))
        self.assertIn("added 'blue pen'", commands.run(lily, "/entity add blue pen object/tool"))
        self.assertIn("removed 'blue pen'", commands.run(lily, "/entity remove blue pen"))
        self.assertIn("scanned 1 chat(s)", commands.run(lily, "/entity scan"))
        self.assertIn("Usage", commands.run(lily, "/entity add pen"))
        self.assertIn("Usage", commands.run(lily, "/entity nonsense"))


if __name__ == "__main__":
    unittest.main()
