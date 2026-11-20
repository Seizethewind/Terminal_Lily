"""Runs a task one step at a time: a retry cap per step, and finished results passed on."""
from lily.self import planner
from lily.self.sub_agent import SubAgent
from lily.utils.errors import LilyError

CLIP = 300


class StepRunner:
    def __init__(self, lily, kit):
        self.lily, self.kit = lily, kit

    def plan(self, task_id, task):
        self.kit.steps.add(task_id, planner.make_plan(self.kit.models, task, self.kit.cfg.limits))

    def run(self, task_id, role, task, kind, notes=()):
        """Do every step that is not done yet (a takeover continues where the worker stopped)."""
        steps = self.kit.steps
        if not steps.rows(task_id):
            steps.add(task_id, [task])
        rows = steps.rows(task_id)
        for n, title, status, _, _ in rows:
            if status != "done":
                self._step(task_id, role, task, kind, (n, len(rows), title), notes)
                notes = ()
        return self._summary(task_id)

    def _step(self, task_id, role, task, kind, where, notes):
        n, total, title = where
        hive, steps = self.kit.hive, self.kit.steps
        text = title if total == 1 else f"Step {n} of {total}: {title}\n\nThe whole task, for context: {task}"
        done = [f"Step {row[0]} ({row[1]}): {row[4][:CLIP]}" for row in steps.rows(task_id) if row[2] == "done"]
        error = None
        for attempt in range(max(1, self.kit.cfg.limits["step_tries"])):
            steps.mark(task_id, n, "running", add_try=True)
            hive.set_state(task_id, f"{'Lily, ' if kind == 'lily' else ''}step {n} of {total}")
            hive.note(task_id, title)
            try:
                result = SubAgent(self.lily, self.kit, task_id, role, text, kind, notes, done).run()
            except Exception as err:   # noqa: BLE001 - any failure counts as a failed try
                error, notes = err, hive.trail(task_id)
                continue
            steps.mark(task_id, n, "done", result=result)
            return
        steps.mark(task_id, n, "failed")
        raise LilyError(f"step {n} of {total} ({title}) failed after {attempt + 1} tries: {error}")

    def _summary(self, task_id):
        rows = self.kit.steps.rows(task_id)
        if len(rows) == 1:
            return rows[0][4]
        return "\n".join(f"{n}. {title}: {result[:CLIP]}" for n, title, _, _, result in rows)
