import unittest

from lily.orchestrator import Lily
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import make_settings, text_reply
from tests.memory_helpers import setup


class SummaryHistoryExportTests(unittest.TestCase):
    def test_summarize_saves_the_summary_as_a_note(self):
        lily, memory = setup(text_reply("one"), text_reply("two"), text_reply("- they said hi twice"))
        lily.handle("hi")
        lily.handle("hello again")
        self.assertEqual(commands.run(lily, "/summarize"), "saved summary #1")
        self.assertIn("[summary] - they said hi twice", memory.describe_lessons())
        self.assertEqual(len(memory.db.rows("SELECT id FROM runs")), 2)   # the summary is not a run

    def test_summarize_with_no_history_is_an_error(self):
        lily, _ = setup()
        with self.assertRaisesRegex(LilyError, "nothing to summarize"):
            commands.run(lily, "/summarize")

    def test_history_and_export_commands(self):
        lily, memory = setup(text_reply("first answer"), text_reply("second answer"))
        lily.handle("first")
        commands.run(lily, "/good")
        lily.handle("second")
        self.assertIn("lily> first answer", commands.run(lily, "/history 5"))
        self.assertIn("wrote 1 chat(s)", commands.run(lily, "/export"))
        self.assertIn("wrote 2 chat(s)", commands.run(lily, "/export all"))
        self.assertTrue((lily.settings.data_dir / "dataset.jsonl").is_file())

    def test_commands_explain_a_missing_layer(self):
        with self.assertRaisesRegex(LilyError, "memory layer is not installed"):
            commands.run(Lily(make_settings()), "/stats")

    def test_database_lives_in_the_data_dir_and_opens_lazily(self):
        lily, memory = setup()
        self.assertFalse((lily.settings.data_dir / "lily.db").exists())
        memory.stats()
        self.assertTrue((lily.settings.data_dir / "lily.db").exists())


if __name__ == "__main__":
    unittest.main()
