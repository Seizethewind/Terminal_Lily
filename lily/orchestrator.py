"""MAIN orchestrator: owns the state, the router and the agent loop."""
from lily.agent_loop import AgentLoop
from lily.router import Router
from lily.state import State
from lily.utils.errors import LilyError


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
        return self.loop.run(self.state, text)

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
