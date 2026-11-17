"""Tests for the self layer: router fallback, hive approvals, task log and chat memory."""
import tempfile
import threading
import unittest
import time
from pathlib import Path

from lily.llm.base import Reply
from lily.self.chat_memory import ChatMemory
from lily.self.config import SelfConfig
from lily.self.hive_mind import HiveMind
from lily.self.router import ModelRouter
from lily.self.task_completion import TaskLog
from lily.utils.errors import LLMError


class FakeProvider:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, 0

    def chat(self, payload):
        self.calls += 1
        if self.fail:
            raise LLMError("down")
        return Reply({"model": payload["model"]}, "fake")


def make_router(workers_fail=True, lily_fail=False):
    cfg = SelfConfig({"roles": {"coder": "heavy"}})
    providers = {"workers": FakeProvider(workers_fail), "lily": FakeProvider(lily_fail)}
    return ModelRouter(cfg, providers, clock=lambda: 0.0)


class RouterTests(unittest.TestCase):
    def test_worker_falls_back_to_lily(self):
        models = make_router()
        reply = models.chat("worker", "normal", [])
        self.assertEqual(reply.data["model"], "auto")
        self.assertEqual(models.providers["lily"].calls, 1)

    def test_all_routers_down(self):
        with self.assertRaises(LLMError):
            make_router(lily_fail=True).chat("worker", "normal", [])

    def test_breaker_skips_a_failing_router(self):
        models = make_router()
        for _ in range(4):
            models.chat("worker", "normal", [])
        self.assertEqual(models.providers["workers"].calls, 3)

    def test_tier_follows_role_size_and_load(self):
        models = make_router()
        self.assertEqual(models.tier("coder"), "heavy")
        self.assertEqual(models.tier("nobody"), "normal")
        self.assertEqual(models.tier("nobody", "x" * 2000), "heavy")
        models.busy = 3
        self.assertEqual(models.tier("coder"), "normal")


class HiveTests(unittest.TestCase):
    def test_approval_round_trip(self):
        hive, result = HiveMind(), []
        thread = threading.Thread(target=lambda: result.append(hive.request(1, "run ls", 5)))
        thread.start()
        while not hive.pending():
            time.sleep(0.01)
        key = hive.pending()[0][0]
        self.assertTrue(hive.answer(key, True))
        thread.join()
        self.assertEqual(result, [True])

    def test_no_answer_means_no(self):
        hive = HiveMind()
        self.assertFalse(hive.request(1, "run ls", 0.01))
        self.assertFalse(hive.answer(1, True))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_task_log(self):
        log = TaskLog(self.path / "t.db")
        task_id = log.start("coder", "fix it")
        self.assertEqual(log.completed(), [])
        log.finish(task_id, "done", "fixed", "worker")
        self.assertEqual(len(log.unseen()), 1)
        log.mark_seen([task_id])
        self.assertEqual(log.unseen(), [])
        self.assertEqual(log.completed()[0][3], "done")

    def test_running_task_fails_after_restart(self):
        TaskLog(self.path / "t.db").start("coder", "fix it")
        self.assertEqual(TaskLog(self.path / "t.db").completed()[0][3], "failed")

    def test_chat_memory_survives_a_restart(self):
        ChatMemory(self.path / "c.db").save_turn("my cat is called Miso", "Cute name!")
        memory = ChatMemory(self.path / "c.db")
        self.assertEqual(memory.earlier(5), [("my cat is called Miso", "Cute name!")])
        self.assertEqual(len(memory.search("how is Miso doing")), 1)
        memory.add_fact("likes tea")
        memory.add_fact("likes tea")
        self.assertEqual(memory.facts(), ["likes tea"])


if __name__ == "__main__":
    unittest.main()
