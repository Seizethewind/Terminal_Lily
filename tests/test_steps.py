"""Tests for task steps: planning, one step at a time, retries, takeover and resume."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.llm.base import Reply
from lily.self import planner
from lily.self.dispatcher import Dispatcher
from lily.self.hive_mind import HiveMind
from lily.self.step_log import StepLog
from lily.self.task_completion import TaskLog
from lily.utils.errors import LilyError, LLMError

LIMITS = {"max_workers": 3, "step_tries": 2, "max_plan_steps": 4, "plan_min_chars": 0}
PLAN = "1. one\n2. two\n3. three"


def reply(text):
    return Reply({"choices": [{"message": {"content": text}}]}, "fake")


class FakeAgent:
    """Stands in for SubAgent: records each call and fails as often as the test says."""
    calls, fail = [], {}   # fail: (kind, 'Step 2 of 3') -> how many times to fail

    def __init__(self, lily, kit, task_id, role, task, kind="worker", notes=(), done=()):
        self.step, self.kind, self.done = task.split(":")[0], kind, done

    def run(self):
        FakeAgent.calls.append((self.kind, self.step, len(self.done)))
        key = (self.kind, self.step)
        if FakeAgent.fail.get(key, 0) > 0:
            FakeAgent.fail[key] -= 1
            raise LilyError("boom")
        return f"did {self.step}"


class StepTests(unittest.TestCase):
    def setUp(self):
        FakeAgent.calls, FakeAgent.fail = [], {}
        self.dir = tempfile.TemporaryDirectory()
        path = Path(self.dir.name) / "t.db"
        models = SimpleNamespace(busy=0, tier=lambda role, task: "light", chat=lambda *a: reply(PLAN))
        kit = SimpleNamespace(cfg=SimpleNamespace(limits=dict(LIMITS)), hive=HiveMind(), steps=StepLog(path), models=models)
        self.tasks = TaskLog(path)
        kit.tasks = self.tasks
        self.dispatcher = Dispatcher(None, kit, self.tasks)
        patch = mock.patch("lily.self.step_runner.SubAgent", FakeAgent)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.dir.cleanup)

    def wait(self, status):
        end = time.time() + 5
        while time.time() < end:
            rows = self.tasks.completed()
            if rows and rows[0][3] == status and self.dispatcher.kit.models.busy == 0:
                return rows[0]
            time.sleep(0.02)
        self.fail(f"task never reached {status}")

    def test_plan_parsing_and_short_tasks(self):
        self.assertEqual(planner.parse_steps("1. a\n2) b\nnot a step\n3. c", 2), ["a", "b"])
        models = SimpleNamespace(tier=lambda *a: "light", chat=lambda *a: self.fail("short tasks need no plan"))
        self.assertEqual(planner.make_plan(models, "do it", {**LIMITS, "plan_min_chars": 140}), ["do it"])

    def test_planning_failure_or_one_step_means_just_the_task(self):
        def down(*args):
            raise LLMError("down")
        broken = SimpleNamespace(tier=lambda *a: "light", chat=down)
        single = SimpleNamespace(tier=lambda *a: "light", chat=lambda *a: reply("1. only one"))
        self.assertEqual(planner.make_plan(broken, "a task", LIMITS), ["a task"])
        self.assertEqual(planner.make_plan(single, "a task", LIMITS), ["a task"])

    def test_steps_run_in_order_and_pass_results_on(self):
        self.dispatcher.submit("coder", "build a thing")
        row = self.wait("done")
        self.assertEqual(FakeAgent.calls, [("worker", f"Step {n} of 3", n - 1) for n in (1, 2, 3)])
        self.assertIn("2. two: did Step 2 of 3", row[5])

    def test_a_step_is_retried_before_giving_up(self):
        FakeAgent.fail = {("worker", "Step 2 of 3"): 1}
        self.dispatcher.submit("coder", "build a thing")
        row = self.wait("done")
        self.assertEqual(row[4], "worker")
        self.assertEqual([c[1] for c in FakeAgent.calls].count("Step 2 of 3"), 2)

    def test_lily_takes_over_at_the_failed_step_not_at_the_start(self):
        FakeAgent.fail = {("worker", "Step 2 of 3"): 9}
        self.dispatcher.submit("coder", "build a thing")
        row = self.wait("done")
        self.assertEqual(row[4], "lily")
        self.assertEqual([c[1] for c in FakeAgent.calls if c[0] == "lily"], ["Step 2 of 3", "Step 3 of 3"])

    def test_a_failed_task_resumes_with_only_the_steps_left(self):
        FakeAgent.fail = {("worker", "Step 2 of 3"): 9, ("lily", "Step 2 of 3"): 9}
        task_id = self.dispatcher.submit("coder", "build a thing")
        self.wait("failed")
        self.assertIn("step 2 of 3", self.dispatcher.kit.steps.progress(task_id))
        before = len(FakeAgent.calls)
        FakeAgent.fail = {}
        self.dispatcher.resume(task_id)
        self.wait("done")
        self.assertEqual([c[1] for c in FakeAgent.calls[before:]], ["Step 2 of 3", "Step 3 of 3"])

    def test_only_failed_tasks_can_be_resumed(self):
        with self.assertRaises(LilyError):
            self.dispatcher.resume(999)
        task_id = self.dispatcher.submit("coder", "build a thing")
        self.wait("done")
        with self.assertRaises(LilyError):
            self.dispatcher.resume(task_id)


if __name__ == "__main__":
    unittest.main()
