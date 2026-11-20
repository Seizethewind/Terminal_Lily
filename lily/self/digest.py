"""Keeps a short rolling summary of old chats, refreshed in the background every few turns."""
import threading

from lily.self import summarizer
from lily.utils.logger import get_logger

log = get_logger("self.digest")
CHUNK = 40   # turns folded in per update


class Digest:
    def __init__(self, memory, models, limits):
        self.memory, self.models, self.limits = memory, models, limits
        self.busy = threading.Lock()

    def due(self):
        return self.memory.count_since(self.memory.summary()[1]) >= self.limits["summary_every"]

    def maybe_run(self):
        """Start an update in the background when enough new turns piled up. Never blocks the chat."""
        if self.due() and self.busy.acquire(blocking=False):
            threading.Thread(target=self._background, daemon=True).start()

    def _background(self):
        try:
            self.update()
        except Exception:   # noqa: BLE001 - a missing summary is never worth an error
            log.exception("could not update the chat summary")
        finally:
            self.busy.release()

    def update(self):
        """Fold the next turns into the summary now. Returns the summary."""
        text, upto = self.memory.summary()
        turns = self.memory.since(upto, CHUNK)
        if not turns:
            return text
        fresh = summarizer.summarize(self.models, text, turns, self.limits["summary_chars"])
        self.memory.save_summary(fresh, turns[-1][0])
        return fresh
