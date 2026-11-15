import unittest

from lily.rag.chunker import chunk
from lily.rag.retriever import find, to_match
from lily.rag.store import Store


class ChunkerTests(unittest.TestCase):
    def test_short_text_is_one_chunk(self):
        self.assertEqual(chunk("hello\n\nworld", size=100), ["hello\n\nworld"])

    def test_paragraphs_are_grouped_up_to_the_size(self):
        text = "\n\n".join(["a" * 40, "b" * 40, "c" * 40])
        chunks = chunk(text, size=90)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("a") and chunks[1] == "c" * 40)

    def test_a_long_paragraph_is_cut_without_losing_words(self):
        words = [f"word{n}" for n in range(200)]
        chunks = chunk(" ".join(words), size=100)
        self.assertTrue(all(len(c) <= 100 for c in chunks))
        self.assertEqual(" ".join(chunks).split(), words)

    def test_empty_text_gives_no_chunks(self):
        self.assertEqual(chunk("  \n\n  "), [])


class RetrieverTests(unittest.TestCase):
    def test_to_match_keeps_useful_words_once(self):
        self.assertEqual(to_match("What is Termux? termux!"), '"is" OR "termux"')

    def test_to_match_is_safe_for_odd_input(self):
        self.assertEqual(to_match('"quoted" (parens)* NEAR/3 -minus'), '"quoted" OR "parens" OR "near" OR "minus"')
        self.assertEqual(to_match("?!"), "")

    def test_find_labels_each_passage_with_its_source(self):
        store = Store(":memory:")
        store.replace("/n/cats.md", ["cats like boxes"])
        self.assertEqual(find(store, "tell me about cats"), ["[/n/cats.md] cats like boxes"])

    def test_find_with_nothing_to_search_for(self):
        self.assertEqual(find(Store(":memory:"), "?!"), [])
        self.assertEqual(find(Store(":memory:"), "cats", limit=0), [])


if __name__ == "__main__":
    unittest.main()
