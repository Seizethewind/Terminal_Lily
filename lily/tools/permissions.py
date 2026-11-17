"""Asks the user before a tool changes anything. Looking around is free (see policy.py)."""
from lily.tools import policy, tidy
from lily.tools.describe import describe


class Permissions:
    def __init__(self, lily):
        self.lily = lily      # lily.confirm is set by the UI after startup
        self.turn = None
        self.grants = set()   # folders the user let Lily save into, for the current message only

    def _grants_now(self, state):
        """A grant ends when the user sends their next message."""
        turn = sum(1 for message in state.messages if message["role"] == "user") if state else 0
        if turn != self.turn:
            self.turn, self.grants = turn, set()
        return self.grants

    def allow(self, tool, args, state=None):
        verdict = policy.decide(tool.name, args)
        if verdict == "allow":
            return True
        grants = self._grants_now(state)
        target = policy.folder(args) if verdict == "write" else None
        if target is not None and policy.covered(target, grants):
            return True
        if not self._ask(tool, args, target):
            return False
        if target is not None:
            grants.add(target)
        return True

    def _ask(self, tool, args, target):
        what, details = describe(tool.name, args)
        lines = [tidy.short(line) for line in details]
        if target is not None:
            lines.append(f"(also covers other files in {tidy.short(target)} for this task)")
        question = "\n".join([f"Lily wants to {what}:", *(f"    {line}" for line in lines)])
        return bool(self.lily.confirm(question))
