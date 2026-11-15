import tempfile
import unittest
from pathlib import Path

from lily.rag.store import Store
from lily.utils.errors import LilyError


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def test_search_finds_stored_text_best_first(self):
        self.store.replace("a.md", ["cats sleep a lot", "dogs bark"])
        self.store.replace("b.md", ["cats cats cats everywhere"])
        rows = self.store.search('"cats"', 5)
        self.assertEqual([source for source, _ in rows], ["b.md", "a.md"])

    def test_stemming_matches_word_forms(self):
        self.store.replace("a.md", ["she is running fast"])
        self.assertEqual(len(self.store.search('"run"', 5)), 1)

    def test_replace_overwrites_the_same_source(self):
        self.store.replace("a.md", ["old text"])
        self.store.replace("a.md", ["new text"])
        self.assertEqual(self.store.search('"old"', 5), [])
        self.assertEqual(self.store.sources(), [("a.md", 1)])

    def test_limit_is_respected(self):
        self.store.replace("a.md", [f"note {n} apple" for n in range(6)])
        self.assertEqual(len(self.store.search('"apple"', 2)), 2)

    def test_sources_and_forget(self):
        self.store.replace("a.md", ["one", "two"])
        self.store.replace("b.md", ["three"])
        self.assertEqual(self.store.sources(), [("a.md", 2), ("b.md", 1)])
        self.assertEqual(self.store.forget("a.md"), 2)
        self.assertEqual(self.store.forget("a.md"), 0)
        self.assertEqual(self.store.sources(), [("b.md", 1)])

    def test_bad_query_syntax_is_a_lily_error(self):
        with self.assertRaises(LilyError):
            self.store.search('"unterminated', 5)

    def test_unusable_database_path_is_a_lily_error(self):
        blocker = Path(tempfile.mkdtemp()) / "file"
        blocker.write_text("not a folder", encoding="utf-8")
        with self.assertRaisesRegex(LilyError, "cannot open"):
            Store(blocker / "rag.db")


if __name__ == "__main__":
    unittest.main()
