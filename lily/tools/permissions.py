"""Asks the user before a tool runs (every tool, for now)."""
import json


def _short(args, limit=1000):
    text = json.dumps(args, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "..."


class Permissions:
    def __init__(self, lily):
        self.lily = lily   # lily.confirm is set by the UI after startup

    def allow(self, tool, args):
        question = f"Lily wants to run {tool.name} {_short(args)} - allow?"
        return bool(self.lily.confirm(question))
