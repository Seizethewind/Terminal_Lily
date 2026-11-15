import unittest

from lily.memory import run_log
from lily.memory.db import Database
from lily.memory.entity_taxonomy import EntityTaxonomy
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply
from tests.memory_helpers import setup

TEXT = "My dog and my cat went to Manila by bus. The dog liked the phone."


def taxonomy():
    db = Database(":memory:")
    return db, EntityTaxonomy(lambda: db)


def file_chat(db, tax, question="q", answer=TEXT):
    return tax.index_run(run_log.record(db, {"user_text": question, "answer": answer}), question, answer)


class EntityTaxonomyTests(unittest.TestCase):
    def test_report_is_a_tree_of_the_three_classes(self):
        db, tax = taxonomy()
        self.assertEqual(file_chat(db, tax), 5)
        lines = tax.report().splitlines()
        self.assertEqual(lines[0], "entity")
        self.assertIn("  animal: dog x2, cat x1", lines)
        self.assertIn("location", lines)
        self.assertIn("  city: manila x1", lines)
        self.assertIn("  vehicle: bus x1", lines)
        self.assertLess(lines.index("entity"), lines.index("location"))
        self.assertLess(lines.index("location"), lines.index("object"))

    def test_empty_report_explains_what_to_do(self):
        self.assertIn("nothing filed yet", taxonomy()[1].report())

    def test_filing_a_chat_twice_does_not_duplicate(self):
        db, tax = taxonomy()
        run = run_log.record(db, {"user_text": "q", "answer": TEXT})
        tax.index_run(run, "q", TEXT)
        tax.index_run(run, "q", TEXT)
        self.assertEqual(db.rows("SELECT count(*) FROM entity_mentions"), [(5,)])

    def test_show_a_class_or_a_subclass(self):
        db, tax = taxonomy()
        file_chat(db, tax)
        self.assertIn("2x dog  [animal]  in 1 chat(s)", tax.show("entity"))
        self.assertNotIn("dog", tax.show("object/device"))
        self.assertIn("phone", tax.show("object/device"))
        self.assertIn("nothing filed under location/water", tax.show("location/water"))
        with self.assertRaises(LilyError):
            tax.show("animals")

    def test_find_lists_the_chats_that_mention_a_word(self):
        db, tax = taxonomy()
        file_chat(db, tax, question="tell me about my dog")
        self.assertEqual(tax.find("Dog"), "chat #1: tell me about my dog")
        self.assertIn("no chat mentions 'whale'", tax.find("whale"))

    def test_add_a_word_then_scan_old_chats(self):
        db, tax = taxonomy()
        run_log.record(db, {"user_text": "q", "answer": "I met Seize at the cafe"})
        self.assertIn("added 'seize' as entity > person", tax.add("Seize", "entity/person"))
        self.assertIn("added 'cafe' as location > place", tax.add("cafe", "location/place"))
        self.assertEqual(tax.scan(), "scanned 1 chat(s), found 2 word(s) from the taxonomy")
        self.assertIn("person: seize x1", tax.report())

    def test_remove_only_your_own_words(self):
        db, tax = taxonomy()
        tax.add("seize", "entity/person")
        self.assertIn("removed 'seize'", tax.remove("seize"))
        with self.assertRaisesRegex(LilyError, "not one you added"):
            tax.remove("dog")


class EntityFlowTests(unittest.TestCase):
    def test_every_turn_is_filed_as_it_happens(self):
        lily, memory = setup(text_reply("Dogs are loyal."))
        lily.handle("tell me about Japan")
        rows = memory.db.rows("SELECT name, cls, sub FROM entity_mentions ORDER BY name")
        self.assertEqual(rows, [("dog", "entity", "animal"), ("japan", "location", "country")])

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
