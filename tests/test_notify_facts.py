"""Tests for phone notifications and for listing and removing remembered facts."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.self.chat_memory import ChatMemory
from lily.self.dispatcher import Dispatcher
from lily.self.hive_mind import HiveMind
from lily.self.notifier import Notifier
from lily.self.step_log import StepLog
from lily.self.task_completion import TaskLog
from lily.ui import commands


class NotifierTests(unittest.TestCase):
    def make(self, found=True, after=30):
        self.calls = []
        finder = (lambda name: "/bin/termux-notification") if found else (lambda name: None)
        return Notifier(True, after, lambda command, **options: self.calls.append(command), finder, background=False)

    def test_off_without_the_termux_api_tools(self):
        notifier = self.make(found=False)
        self.assertFalse(notifier.enabled)
        self.assertFalse(notifier.send("a", "b"))
        self.assertEqual(self.calls, [])

    def test_send_builds_the_termux_command(self):
        self.assertTrue(self.make().send("Title", "Body"))
        self.assertEqual(self.calls[0], ["termux-notification", "--title", "Title", "--content", "Body"])

    def test_quick_successes_stay_quiet_slow_and_failed_tasks_speak(self):
        notifier = self.make(after=30)
        self.assertFalse(notifier.task_finished(1, "job", "done", "ok", 5))
        self.assertTrue(notifier.task_finished(2, "job", "done", "ok", 40))
        self.assertIn("task #2 done", self.calls[-1][2])
        self.assertTrue(notifier.task_finished(3, "job", "failed", "boom", 1))
        self.assertIn("task #3 failed", self.calls[-1][2])

    def test_a_broken_runner_never_raises(self):
        def broken(*args, **options):
            raise OSError("no")
        Notifier(True, 0, broken, lambda name: "x", background=False).send("a", "b")

    def test_the_hive_tells_the_phone_when_a_worker_waits_and_survives_a_failure(self):
        seen = []
        hive = HiveMind(lambda task, text: seen.append((task, text)))
        self.assertFalse(hive.request(7, "run ls", 0.01))
        self.assertEqual(seen, [(7, "run ls")])

        def broken(*args):
            raise RuntimeError("x")
        self.assertFalse(HiveMind(broken).request(1, "x", 0.01))

    def test_a_finished_task_notifies_the_phone(self):
        path = Path(tempfile.mkdtemp()) / "t.db"
        models = SimpleNamespace(busy=0, tier=lambda *a: "light", role_tier=lambda role: "light")
        limits = {"max_workers": 3, "step_tries": 1, "max_plan_steps": 4, "plan_min_chars": 1000}
        kit = SimpleNamespace(cfg=SimpleNamespace(limits=limits), hive=HiveMind(), steps=StepLog(path),
                              models=models, notifier=self.make(after=0))
        agent = SimpleNamespace(run=lambda: "all done")
        with mock.patch("lily.self.step_runner.SubAgent", lambda *a, **k: agent):
            Dispatcher(None, kit, TaskLog(path)).submit("coder", "fix it")
            end = time.time() + 5
            while not self.calls and time.time() < end:
                time.sleep(0.02)
        self.assertEqual(self.calls[0][2], "Lily: task #1 done")
        self.assertIn("fix it", self.calls[0][4])


class FactTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.memory = ChatMemory(Path(self.dir.name) / "c.db")
        self.notifier = Notifier(True, 30, lambda *a, **k: None, lambda name: "x", background=False)
        sub = SimpleNamespace(memory=self.memory, notifier=self.notifier,
                              remember=lambda text: self.memory.add_fact(text) or "Saved.")
        self.lily = SimpleNamespace(router=SimpleNamespace(get=lambda name: sub))

    def run_command(self, name, *args):
        return commands.COMMANDS[name][0](self.lily, list(args))

    def test_list_add_and_remove_facts(self):
        self.assertIn("Nothing saved", self.run_command("facts"))
        self.assertEqual(self.run_command("remember", "likes", "tea"), "Saved.")
        self.run_command("remember", "has", "a", "dog", "named", "Max")
        listing = self.run_command("facts")
        self.assertIn("#1 likes tea", listing)
        self.assertIn("#2 has a dog named Max", listing)
        self.assertEqual(self.run_command("unremember", "#1"), "Removed.")
        self.assertNotIn("likes tea", self.run_command("facts"))
        self.assertIn("no fact #9", self.run_command("unremember", "9"))
        self.assertIn("Usage", self.run_command("unremember"))
        self.assertIn("Usage", self.run_command("remember"))

    def test_the_notify_command_explains_and_tests(self):
        self.assertIn("30 seconds", self.run_command("notify"))
        self.assertIn("Sent", self.run_command("notify", "test"))
        self.notifier.enabled = False
        self.assertIn("pkg install termux-api", self.run_command("notify"))


if __name__ == "__main__":
    unittest.main()
