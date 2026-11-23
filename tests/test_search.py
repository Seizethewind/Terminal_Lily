import unittest

from lily.memory import run_log
from lily.memory.db import Database
from lily.memory.search import Search
from lily.memory.taxonomy.service import Taxonomy
from lily.utils.errors import LilyError

ANIME = "study/entertainment/anime"


def add(db, user, answer="ok"):
    return run_log.record(db, {"profile": "p", "routed_via": "x", "user_text": user, "answer": answer,
                               "tools": "", "steps": 1, "latency_ms": 1, "error": ""})


def make():
    db = Database(":memory:")
    tax = Taxonomy(lambda: db)
    return db, tax, Search(lambda: db, tax, lambda: None)


class ChatSearchTests(unittest.TestCase):
    def test_finds_chats_by_words_in_question_or_answer(self):
        db, _, search = make()
        add(db, "tell me about elden ring bosses")
        add(db, "weather today", "sunny with elden light")
        add(db, "unrelated")
        out = search.run("elden")
        self.assertIn("#1", out)
        self.assertIn("#2", out)
        self.assertNotIn("#3", out)

    def test_all_words_first_then_any(self):
        db, _, search = make()
        add(db, "elden ring")
        add(db, "elden only")
        first = search.run("elden ring").splitlines()
        self.assertTrue(first[1].startswith("  #1"))
        self.assertEqual(len(first), 2)
        self.assertIn("#2", search.run("elden zzzz"))

    def test_paging_and_chat_view(self):
        db, _, search = make()
        for n in range(8):
            add(db, f"zelda note {n}")
        self.assertIn("/search more", search.run("zelda"))
        self.assertIn("Chats 6-8", search.more())
        self.assertEqual(search.more(), "no more chats")
        self.assertIn("you> zelda note 0", search.chat(1))
        with self.assertRaises(LilyError):
            search.chat(99)

    def test_category_filter_only_kind_and_nothing_found(self):
        db, tax, search = make()
        add(db, "naruto fight")
        add(db, "naruto recipe")
        tax.classify("run", "1", ANIME)
        out = search.run(f"naruto in {ANIME}")
        self.assertIn("#1", out)
        self.assertNotIn("#2", out)
        self.assertIn("nothing found", search.run("naruto only notes"))
        self.assertIn("nothing found", search.run("qqqq"))

    def test_words_are_searched_and_empty_query_explains(self):
        _, _, search = make()
        search.db.write("INSERT INTO dictionary(term, label, meaning, path, aliases, ts) VALUES (?,?,?,?,?,?)",
                        ("naruto", "Naruto", "ninja manga", ANIME, "", "t"))
        self.assertIn("Naruto", search.run("ninja only words"))
        with self.assertRaises(LilyError):
            search.run("the")
        with self.assertRaises(LilyError):
            Search(lambda: search.db, search.tax, lambda: None).more()

    def test_old_chats_are_indexed_and_plain_fallback_works(self):
        db, tax, _ = make()
        add(db, "old chat about gacha")
        db.db.execute("DROP TABLE runs_fts")
        db.db.execute("DROP TRIGGER runs_fts_insert")
        again = Database.__new__(Database)
        again.db = db.db
        again.fts = again._start_index()
        self.assertTrue(again.fts)
        self.assertIn("#1", Search(lambda: again, tax, lambda: None).run("gacha"))
        again.fts = False
        self.assertIn("#1", Search(lambda: again, tax, lambda: None).run("gacha"))


if __name__ == "__main__":
    unittest.main()
