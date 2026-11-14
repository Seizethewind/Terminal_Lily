"""Decides which sub orchestrator handles the next step."""
from lily.utils.errors import LilyError

# step type returned by the LLM -> sub orchestrator that must act (None = done)
ROUTES = {"final": None, "tool_call": "tools"}


class Router:
    def __init__(self):
        self._subs = {}

    def register(self, sub):
        self._subs[sub.name] = sub

    def get(self, name):
        return self._subs.get(name)

    def names(self):
        return sorted(self._subs)

    def route(self, result):
        kind = result.get("type")
        if kind not in ROUTES:
            raise LilyError(f"unknown step type from the model: {kind!r}")
        return ROUTES[kind]
