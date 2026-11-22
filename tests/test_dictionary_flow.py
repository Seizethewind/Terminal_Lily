import tempfile
import unittest
from pathlib import Path

from lily.memory import dict_seed, dict_store
from lily.memory.taxonomy.tree import Tree, load_config
from lily.state import State
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply
from tests.memory_helpers import setup
from tests.test_dictionary import SHONEN, make


class SeedTests(unittest.TestCase):
    def test_every_shipped_starter_word_loads_with_a_real_category(self):
        _, tax, book = make()
        message = book.load()
        self.assertIn("skipped 0", message)
        self.assertGreaterEqual(len(dict_store.everything(book.db)), 14)
        self.assertTrue(all(item["path"] in Tree(load_config()).nodes for item in dict_store.everything(book.db)))

    def test_words_you_already_have_are_not_changed_and_bad_files_are_errors(self):
        _, _, book = make()
        book.add("Minecraft", "my own meaning")
        self.assertIn("kept 1", book.load())
        self.assertIn("my own meaning", book.show("minecraft"))
        bad = Path(tempfile.mkdtemp()) / "d.toml"
        bad.write_text('[[entry]]\nterm = "X1"\nmeaning = "m"\npath = "study/none/x"\n', encoding="utf-8")
        self.assertIn("skipped 1", dict_seed.load(book, bad))
        with self.assertRaises(LilyError):
            dict_seed.load(book, bad.with_name("missing.toml"))


class WiringTests(unittest.TestCase):
    def test_the_command_and_the_prompt_hook_are_wired_in(self):
        lily, memory = setup(text_reply("ok"))
        self.assertIn("0 word(s)", commands.run(lily, "/dict"))
        self.assertIn("saved 'naruto'", commands.run(lily, f"/dict add Naruto = ninja manga @ {SHONEN}"))
        self.assertIn("ninja manga", commands.run(lily, "/dict naruto"))
        self.assertIn("also called", commands.run(lily, "/dict alias naruto = uzumaki"))
        self.assertIn("Naruto", commands.run(lily, "/dict find ninja"))
        self.assertIn("Usage", commands.run(lily, "/dict add oops"))
        state = State()
        memory.run(state, query="who is uzumaki?")
        self.assertEqual(state.context, ["[dictionary] Naruto: ninja manga"])
        memory.run(state, query="")
        self.assertEqual(len(state.context), 1)
        self.assertIn("removed", commands.run(lily, "/dict remove naruto"))


if __name__ == "__main__":
    unittest.main()
