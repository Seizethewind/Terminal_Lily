"""Asks the user before a tool runs (every tool, for now)."""
from lily.tools.describe import describe


class Permissions:
    def __init__(self, lily):
        self.lily = lily   # lily.confirm is set by the UI after startup

    def allow(self, tool, args):
        what, details = describe(tool.name, args)
        question = "\n".join([f"Lily wants to {what}:", *(f"    {line}" for line in details)])
        return bool(self.lily.confirm(question))
