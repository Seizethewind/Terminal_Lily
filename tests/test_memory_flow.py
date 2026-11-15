import tempfile
import unittest
from pathlib import Path

from lily.tools.orchestrator import ToolsOrchestrator
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply, tool_reply
from tests.memory_helpers import Hello, setup


class RecordingTests(unittest.TestCase):
    def test_a_turn_is_logged_with_profile_and_model(self):
        lily, memory = setup(text_reply("fine"))
        lily.handle("write some code")
        run = memory.db.rows("SELECT user_text, answer, profile, routed_via, steps, error FROM runs")[0]
        self.assertEqual(run, ("write some code", "fine", "smart", "prov/model", 1, ""))
        self.assertEqual(memory.last_run_id, 1)

    def test_tools_used_are_logged(self):
        lily, memory = setup(tool_reply("hello", {}), text_reply("done"))
        tools = ToolsOrchestrator(lily, plugins_dir=Path(tempfile.mkdtemp()), mcp_loader=lambda lily: ([], []))
        tools.registry.register(Hello(lily))
        lily.register(tools)
        lily.handle("say hello")
        self.assertEqual(lily.loop.last, {"tools": ["hello"], "steps": 2})
        self.assertEqual(memory.history(), "you> say hello\nlily> done")
        self.assertIn('["hello"]', memory.db.rows("SELECT tools FROM runs")[0][0])

    def test_failed_turns_are_logged_and_still_raise(self):
        lily, memory = setup()   # no replies left: the provider raises
        with self.assertRaises(IndexError):
            lily.handle("hello")
        self.assertIn("pop from empty list", memory.db.rows("SELECT error FROM runs")[0][0])

    def test_a_broken_memory_never_breaks_the_chat(self):
        lily, memory = setup(text_reply("still works"))
        memory.run = lambda state, record=None: 1 / 0
        self.assertEqual(lily.handle("hello"), "still works")


class FeedbackAndLessonTests(unittest.TestCase):
    def test_rating_needs_a_previous_answer(self):
        _, memory = setup()
        with self.assertRaisesRegex(LilyError, "nothing to rate"):
            memory.rate(1)

    def test_good_and_bad_commands_rate_the_last_answer(self):
        lily, memory = setup(text_reply("a"))
        lily.handle("hi")
        self.assertIn("good", commands.run(lily, "/good nice"))
        self.assertIn("bad", commands.run(lily, "/bad"))
        self.assertEqual(memory.db.rows("SELECT rating FROM feedback"), [(-1,)])
        self.assertEqual(" ".join(commands.run(lily, "/stats").split()), "auto runs 1 good 0 bad 1")

    def test_lessons_come_back_through_the_notes(self):
        lily, _ = setup(text_reply("ok"))
        self.assertEqual(commands.run(lily, "/lesson Lily prefers tea over coffee"), "saved lesson #1")
        lily.handle("what does Lily prefer, tea or coffee?")
        self.assertIn("[lesson:1]", lily.state.context[0])
        self.assertIn("tea", commands.run(lily, "/lessons"))

    def test_unlearn_removes_the_lesson_everywhere(self):
        lily, _ = setup()
        commands.run(lily, "/lesson Mochi is a cat")
        self.assertEqual(commands.run(lily, "/unlearn 1"), "removed lesson #1")
        self.assertEqual(lily.router.get("rag").search("Mochi"), [])
        self.assertEqual(commands.run(lily, "/unlearn 1"), "no lesson #1")
        self.assertIn("Usage", commands.run(lily, "/unlearn abc"))

    def test_lessons_work_without_the_rag_layer(self):
        lily, _ = setup(with_rag=False)
        self.assertEqual(commands.run(lily, "/lesson be brief"), "saved lesson #1")
        self.assertEqual(commands.run(lily, "/unlearn 1"), "removed lesson #1")
        self.assertIn("Usage", commands.run(lily, "/lesson"))


if __name__ == "__main__":
    unittest.main()
