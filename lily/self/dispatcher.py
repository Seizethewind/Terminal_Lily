"""Runs workers in the background, and hands a failed task to Lily to finish."""
import threading
import time

from lily.self import namer
from lily.self.step_runner import StepRunner
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("self.dispatch")
NAME_MIN = 50   # shorter tasks are their own title


class Dispatcher:
    def __init__(self, lily, kit, tasks):
        self.lily, self.kit, self.tasks = lily, kit, tasks
        self.lock = threading.Lock()
        self.runner = StepRunner(lily, kit)

    def _reserve(self):
        limit = self.kit.cfg.limits["max_workers"]
        with self.lock:
            if self.kit.models.busy >= limit:
                raise LilyError(f"{limit} workers are already busy; wait for one to finish")
            self.kit.models.busy += 1

    def _release(self):
        with self.lock:
            self.kit.models.busy -= 1

    def submit(self, role, task):
        """Start a worker and return its task number at once."""
        self._reserve()
        try:
            task_id = self.tasks.start(role, task)
        except Exception:
            self._release()
            raise
        self._launch(task_id, role, task, planned=False)
        return task_id

    def resume(self, task_id):
        """Run a failed task again: steps that are done stay done."""
        row = self.tasks.get(task_id)
        if row is None or row[3] != "failed":
            raise LilyError(f"task #{task_id} is not a failed task")
        self._reserve()
        self.tasks.reopen(task_id)
        self.kit.steps.reset(task_id)
        self._launch(task_id, row[1], row[2], planned=True)
        return task_id

    def _launch(self, task_id, role, task, planned):
        self.kit.hive.join(task_id, role)
        threading.Thread(target=self._work, args=(task_id, role, task, planned), daemon=True).start()
        if len(task) > NAME_MIN and not planned:
            threading.Thread(target=self._name, args=(task_id, task), daemon=True).start()

    def _name(self, task_id, task):
        try:
            title = namer.make_title(self.kit.models, task)
            if title:
                self.tasks.rename(task_id, title)
        except Exception:   # noqa: BLE001 - a missing title is never worth an error
            log.warning("could not name task %s", task_id)

    def _notify(self, task_id, status, result, seconds):
        """Tell the phone a task is finished. Never raises: it must not stop the worker from being released."""
        try:
            notifier, row = getattr(self.kit, "notifier", None), self.tasks.get(task_id)
            if notifier and row:
                notifier.task_finished(task_id, row[6] or row[2][:50], status, result[:150], seconds)
        except Exception:   # noqa: BLE001
            log.warning("could not notify about task %s", task_id)

    def _work(self, task_id, role, task, planned):
        hive, status, who, started = self.kit.hive, "done", "worker", time.monotonic()
        try:
            try:
                if not planned:
                    self.runner.plan(task_id, task)
                result = self.runner.run(task_id, role, task, "worker")
            except Exception as err:   # noqa: BLE001 - a worker can fail in any way
                log.warning("worker for task %s failed: %s", task_id, err)
                hive.note(task_id, f"the worker failed: {err}")
                hive.set_state(task_id, "Lily is taking over")
                who = "lily"
                result = self.runner.run(task_id, role, task, "lily", hive.trail(task_id))
        except Exception as err:   # noqa: BLE001 - Lily failed too
            log.warning("takeover of task %s failed: %s", task_id, err)
            status, result = "failed", f"nobody could finish it: {err}"
        self.tasks.finish(task_id, status, result, who)
        self._notify(task_id, status, result, time.monotonic() - started)
        hive.leave(task_id)
        self._release()
