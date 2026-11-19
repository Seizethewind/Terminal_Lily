"""Facade for staged writes: stage, show, apply, discard and undo."""
from lily.self import changes
from lily.self.apply import Applier
from lily.self.stage_store import StageStore
from lily.tools import tidy
from lily.utils.errors import ToolError
from lily.utils.paths import in_workplace


class Staging:
    def __init__(self, folder):
        self.store, self.applier = StageStore(folder), Applier(folder)

    def stage_write(self, file, content, append=False):
        """`file` is a resolved path inside the workplace."""
        self.store.stage(file, content, append)
        return (f"Staged {tidy.short(file)} ({len(content)} characters). It is NOT saved yet: "
                "it waits until the user applies it. Tell them what is waiting.")

    def has(self, file):
        return self.store.get(file) is not None

    def read(self, file):
        return self.store.get(file)

    def count(self):
        return len(self.store.snapshot())

    def changes(self, path=None):
        pending = self.store.snapshot()
        if not pending:
            return "No changes are waiting."
        if path:
            file = str(in_workplace(path))
            return changes.diff(file, pending[file]) if file in pending else "That file is not waiting."
        return "\n".join(["Waiting to be saved (nothing is saved until apply):", *changes.describe(pending)])

    def question(self):
        lines = changes.describe(self.store.snapshot())
        return "\n".join(["Lily wants to save these files:", *(f"    {line}" for line in lines)])

    def apply(self):
        items = self.store.take_all()
        if not items:
            return "Nothing is waiting."
        try:
            count = self.applier.apply(items)
        except ToolError:
            self.store.put_back(items)
            raise
        return f"Saved {count} file(s). /undo or the undo_apply tool puts them back."

    def discard(self, path=None):
        target = str(in_workplace(path)) if path else None
        return f"Dropped {self.store.drop(target)} waiting file(s)."

    def undo(self):
        return self.applier.undo()
