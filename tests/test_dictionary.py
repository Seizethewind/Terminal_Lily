import unittest

from lily.memory.db import Database
from lily.memory.dictionary import Dictionary
from lily.memory.taxonomy.service import Taxonomy
from lily.utils.errors import LilyError

SHONEN = "study/entertainment/anime/anime-demographic/shonen"


def make():
    db = Database(":memory:")
    tax = Taxonomy(lambda: db)
    return db, tax, Dictionary(lambda: db, tax)


class DictionaryTests(unittest.TestCase):
    def test_a_word_is_saved_shown_found_and_removed(self):
        _, _, book = make()
        self.assertIn("filed under " + SHONEN, book.add("Naruto", "ninja manga", SHONEN))
        self.assertEqual(book.show("naruto").splitlines()[0], "Naruto  - ninja manga")
        self.assertIn("category: " + SHONEN, book.show("NARUTO"))
        self.assertIn("Naruto", book.find("ninja"))
        self.assertIn("Naruto", book.under("study/entertainment/anime"))
        self.assertEqual(book.remove("naruto"), "removed 'naruto'")
        self.assertIn("not in your dictionary", self._error(book.show, "naruto"))

    def _error(self, fn, *args):
        with self.assertRaises(LilyError) as caught:
            fn(*args)
        return str(caught.exception)

    def test_bad_input_is_explained(self):
        _, _, book = make()
        self.assertIn("not in the taxonomy", self._error(book.add, "x1", "m", "study/nothing/here"))
        self.assertIn("say what it means", self._error(book.add, "word", "  "))
        self.assertIn("2 to 60", self._error(book.add, "a", "m"))
        self.assertIn("2 to 60", self._error(book.add, "a|b", "m"))

    def test_aliases_work_and_cannot_steal_another_word(self):
        _, _, book = make()
        book.add("Fullmetal Alchemist", "manga about alchemy", SHONEN)
        book.add("Naruto", "ninja manga")
        self.assertIn("fma", book.alias("fullmetal alchemist", "FMA, Alchemist Brothers"))
        self.assertIn("also: alchemist brothers, fma", book.show("fma"))
        self.assertIn("already belongs", self._error(book.alias, "naruto", "fma"))
        book.add("Fullmetal Alchemist", "new meaning")   # saving again keeps the aliases
        self.assertIn("fma", book.show("Fullmetal Alchemist"))

    def test_chats_are_filed_by_your_words_even_without_the_category_name(self):
        db, tax, book = make()
        book.add("Naruto", "ninja manga", SHONEN)
        book.add("Nobody", "has no category")
        tax.index_run(1, "I rewatched Naruto yesterday", "Nice, it is a classic.")
        tax.index_run(2, "Tell me about Nobody", "")
        self.assertIn(SHONEN + "  (auto:tree)", tax.of("run", 1))
        self.assertEqual(tax.of("run", 2), "no labels: it is unclassified")
        db.write("DELETE FROM taxonomy_labels")
        db.write("INSERT INTO runs(user_text, answer) VALUES ('my naruto', '')")
        tax.scan()
        self.assertIn(SHONEN, tax.of("run", 1))

    def test_the_meanings_of_words_in_a_message_go_to_the_prompt(self):
        _, _, book = make()
        book.add("Elden Ring", "FromSoftware action game")
        book.add("Valorant", "tactical shooter by Riot")
        book.alias("valorant", "val")
        lines = book.context("Is Elden Ring harder than the others? Also `valorant` in code")
        self.assertEqual(lines, ["[dictionary] Elden Ring: FromSoftware action game"])
        self.assertEqual(len(book.context("val and elden ring")), 2)
        self.assertEqual(book.context("nothing here"), [])

    def test_at_most_five_meanings_are_added(self):
        _, _, book = make()
        for number in range(8):
            book.add(f"word{number}", "meaning")
        self.assertEqual(len(book.context(" ".join(f"word{n}" for n in range(8)))), 5)


if __name__ == "__main__":
    unittest.main()
