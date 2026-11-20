"""Tests for the rolling chat summary: storage, the summarizer, the digest and the brief."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from lily.llm.base import Reply
from lily.self import summarizer
from lily.self.chat_memory import ChatMemory
from lily.self.config import SelfConfig
from lily.self.digest import Digest
from lily.self.orchestrator import SelfOrchestrator

LIMITS = {"summary_every": 2, "summary_chars": 100}


def models(answer="Jayson likes tea."):
    seen = []

    def chat(kind, tier, messages, tools=None):
        seen.append(messages)
        return Reply({"choices": [{"message": {"content": answer}}]}, "fake")
    return SimpleNamespace(tier=lambda role, task: "light", chat=chat, seen=seen)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.memory = ChatMemory(Path(self.dir.name) / "c.db")

    def chats(self, count):
        for n in range(count):
            self.memory.save_turn(f"question {n}", f"answer {n}")

    def test_summary_storage_and_counting(self):
        self.assertEqual(self.memory.summary(), ("", 0))
        self.chats(3)
        self.assertEqual(self.memory.count_since(0), 3)
        turns = self.memory.since(1, 5)
        self.assertEqual([t[0] for t in turns], [2, 3])
        self.memory.save_summary("short", 2)
        self.assertEqual(self.memory.summary(), ("short", 2))
        self.assertEqual(self.memory.count_since(2), 1)

    def test_summarizer_sends_the_old_summary_and_the_new_turns(self):
        fake = models("x" * 500)
        text = summarizer.summarize(fake, "old news", [(1, "hi", "hello")], 100)
        sent = fake.seen[0][1]["content"]
        self.assertTrue("old news" in sent and "user: hi" in sent)
        self.assertEqual(len(text), 100)
        self.assertEqual(summarizer.summarize(models(""), "keep me", [(1, "a", "b")], 100), "keep me")

    def test_digest_folds_turns_in_and_waits_for_more(self):
        digest = Digest(self.memory, models(), LIMITS)
        self.chats(1)
        self.assertFalse(digest.due())
        self.chats(1)
        self.assertTrue(digest.due())
        self.assertEqual(digest.update(), "Jayson likes tea.")
        self.assertEqual(self.memory.summary(), ("Jayson likes tea.", 2))
        self.assertFalse(digest.due())

    def test_the_update_runs_in_the_background(self):
        digest = Digest(self.memory, models(), LIMITS)
        self.chats(2)
        digest.maybe_run()
        end = time.time() + 5
        while not self.memory.summary()[0] and time.time() < end:
            time.sleep(0.02)
        self.assertEqual(self.memory.summary()[0], "Jayson likes tea.")

    def test_a_failing_model_never_breaks_anything(self):
        def down(*args):
            raise RuntimeError("down")
        digest = Digest(self.memory, SimpleNamespace(tier=lambda *a: "light", chat=down), LIMITS)
        self.chats(2)
        digest._background() if digest.busy.acquire() else None
        self.assertEqual(self.memory.summary(), ("", 0))

    def test_the_brief_carries_the_summary(self):
        orchestrator = SelfOrchestrator(SimpleNamespace(), SelfConfig({}), Path(self.dir.name))
        orchestrator.memory.save_summary("Jayson builds Terminal Lily.", 0)
        lines = orchestrator._brief("hello", SimpleNamespace(messages=[]))
        self.assertIn("Jayson builds Terminal Lily.", lines)


if __name__ == "__main__":
    unittest.main()
