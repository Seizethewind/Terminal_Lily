import json
import tempfile
import unittest
from pathlib import Path

from lily.memory import feedback, history, run_log, summarizer
from lily.memory.db import Database
from lily.memory.export_dataset import export
from lily.utils.errors import LilyError


class FakeLLM:
    def __init__(self, result):
        self.result, self.states = result, []

    def run(self, state, **kwargs):
        self.states.append(state)
        return self.result


def filled():
    db = Database(":memory:")
    ids = [run_log.record(db, {"user_text": q, "answer": a, "profile": "smart", "tools": ["shell"]})
           for q, a in [("q1", "a1"), ("q2", "a2"), ("q3", "a3")]]
    run_log.record(db, {"user_text": "q4", "answer": "", "error": "down"})
    return db, ids


class HistoryTests(unittest.TestCase):
    def test_exchanges_are_oldest_first_and_skip_failures(self):
        db, _ = filled()
        self.assertEqual(history.exchanges(db, 10), [("q1", "a1"), ("q2", "a2"), ("q3", "a3")])
        self.assertEqual(history.exchanges(db, 2), [("q3", "a3")])   # the failed q4 takes one slot

    def test_render_shortens_long_text(self):
        text = history.render([("q", "word " * 200)], width=50)
        self.assertIn("lily> word word", text)
        self.assertTrue(text.endswith("..."))


class SummarizerTests(unittest.TestCase):
    def test_summary_text_comes_back_and_uses_the_fast_profile(self):
        llm = FakeLLM({"type": "final", "text": " - they talked\n"})
        self.assertEqual(summarizer.summarize(llm, [("hi", "hello")]), "- they talked")
        self.assertEqual(llm.states[0].profile, "fast")
        self.assertIn("hello", llm.states[0].messages[0]["content"])

    def test_a_tool_call_or_empty_answer_is_an_error(self):
        for result in ({"type": "tool_call", "name": "x"}, {"type": "final", "text": "  "}):
            with self.assertRaises(LilyError):
                summarizer.summarize(FakeLLM(result), [("a", "b")])


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.db, self.ids = filled()
        feedback.rate(self.db, self.ids[0], 1)
        feedback.rate(self.db, self.ids[1], -1)
        self.path = Path(tempfile.mkdtemp()) / "out" / "set.jsonl"

    def lines(self):
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]

    def test_default_exports_only_good_chats(self):
        self.assertEqual(export(self.db, self.path), 1)
        row = self.lines()[0]
        self.assertEqual(row["messages"][0], {"role": "user", "content": "q1"})
        self.assertEqual(row["messages"][1], {"role": "assistant", "content": "a1"})
        self.assertEqual((row["rating"], row["profile"], row["tools"]), (1, "smart", ["shell"]))

    def test_all_exports_every_finished_chat_but_not_failures(self):
        self.assertEqual(export(self.db, self.path, only_good=False), 3)
        self.assertEqual([r["rating"] for r in self.lines()], [1, -1, None])

    def test_unwritable_target_is_a_lily_error(self):
        blocker = Path(tempfile.mkdtemp()) / "file"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaises(LilyError):
            export(self.db, blocker / "set.jsonl")


if __name__ == "__main__":
    unittest.main()
