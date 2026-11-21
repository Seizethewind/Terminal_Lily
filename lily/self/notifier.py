"""Phone notifications through Termux:API, so a finished task or a waiting approval needs no looking."""
import shutil
import subprocess
import threading

from lily.utils.logger import get_logger

log = get_logger("self.notify")


class Notifier:
    def __init__(self, enabled=True, after_seconds=30, runner=subprocess.run, finder=shutil.which, background=True):
        self.enabled = bool(enabled and finder("termux-notification"))   # off without the Termux:API tools
        self.after, self.runner, self.background = after_seconds, runner, background

    def send(self, title, text):
        """Show a notification. Returns False when they are off. Never raises and never blocks."""
        if not self.enabled:
            return False
        if self.background:
            threading.Thread(target=self._run, args=(title, text), daemon=True).start()
        else:
            self._run(title, text)
        return True

    def _run(self, title, text):
        command = ["termux-notification", "--title", title[:80], "--content", text[:300]]
        try:
            self.runner(command, capture_output=True, timeout=15, stdin=subprocess.DEVNULL)
        except Exception:   # noqa: BLE001 - a notification must never break anything
            log.warning("could not show a notification")

    def task_finished(self, task_id, label, status, result, seconds):
        """Tell the user when a task took a while or failed. Quick successes stay quiet."""
        if status == "done" and seconds < self.after:
            return False
        verb = "done" if status == "done" else "failed"
        return self.send(f"Lily: task #{task_id} {verb}", f"{label}: {result}")

    def approval(self, task_id, text):
        """A worker is waiting for the user's yes or no."""
        self.send(f"Lily: task #{task_id} needs your OK", text)
