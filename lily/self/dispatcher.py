"""Runs workers in the background, and hands a failed task to Lily to finish."""
import threading

from lily.self.sub_agent import SubAgent
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("self.dispatch")


class Dispatcher:
    def __init__(self, lily, kit, tasks):
        self.lily, self.kit, self.tasks = lily, kit, tasks
        self.lock = threading.Lock()

    def submit(self, role, task):
        """Start a worker and return its task number at once."""
        limit = self.kit.cfg.limits["max_workers"]
        with self.lock:
            if self.kit.models.busy >= limit:
                raise LilyError(f"{limit} workers are already busy; wait for one to finish")
            self.kit.models.busy += 1
        try:
            task_id = self.tasks.start(role, task)
        except Exception:
            self._release()
            raise
        self.kit.hive.join(task_id, role)
        threading.Thread(target=self._work, args=(task_id, role, task), daemon=True).start()
        return task_id

    def _release(self):
        with self.lock:
            self.kit.models.busy -= 1

    def _work(self, task_id, role, task):
        hive, status, who = self.kit.hive, "done", "worker"
        try:
            try:
                result = self._attempt(task_id, role, task, "worker", ())
            except Exception as err:   # noqa: BLE001 - a worker can fail in any way
                log.warning("worker for task %s failed: %s", task_id, err)
                hive.note(task_id, f"the worker failed: {err}")
                hive.set_state(task_id, "Lily is taking over")
                who = "lily"
                result = self._attempt(task_id, role, task, "lily", hive.trail(task_id))
        except Exception as err:   # noqa: BLE001 - Lily failed too
            log.warning("takeover of task %s failed: %s", task_id, err)
            status, result = "failed", f"nobody could finish it: {err}"
        self.tasks.finish(task_id, status, result, who)
        hive.leave(task_id)
        self._release()

    def _attempt(self, task_id, role, task, kind, notes):
        return SubAgent(self.lily, self.kit, task_id, role, task, kind, notes).run()
