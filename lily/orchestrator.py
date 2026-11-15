"""MAIN orchestrator: owns the state, the router and the agent loop."""
import time

from lily.agent_loop import AgentLoop
from lily.router import Router
from lily.state import State
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("lily")


class Lily:
    def __init__(self, settings):
        self.settings = settings
        self.router = Router()
        self.state = State(settings.system_prompt, settings.profile, settings.max_history)
        self.loop = AgentLoop(self.router, settings.max_steps)
        # Replaced by the UI; the safe default is to refuse.
        self.confirm = lambda question: False

    def register(self, sub):
        self.router.register(sub)

    def handle(self, text):
        started = time.monotonic()
        try:
            answer = self.loop.run(self.state, text)
        except Exception as err:
            self._record(text, "", started, str(err))
            raise
        self._record(text, answer, started)
        return answer

    def _record(self, text, answer, started, error=""):
        """Give the finished turn to the memory layer, if installed. Never fails the chat."""
        memory = self.router.get("memory")
        if memory is None:
            return
        millis = int((time.monotonic() - started) * 1000)
        record = {"user_text": text, "answer": answer, "error": error, "latency_ms": millis, **self.loop.last}
        try:
            memory.run(self.state, record=record)
        except Exception:   # noqa: BLE001 - logging a turn must never break the chat
            log.exception("could not record the run")

    @property
    def model(self):
        """The router model string for the current profile, e.g. 'auto:fast'."""
        return self.settings.profiles[self.state.profile]

    def set_profile(self, name):
        if name not in self.settings.profiles:
            options = ", ".join(self.settings.profiles)
            raise LilyError(f"unknown profile '{name}'. Options: {options}")
        self.state.profile = name

    def reset(self):
        self.state.reset()
