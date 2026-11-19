"""Writes the waiting files into the workplace and remembers how to take it back."""
import json
from pathlib import Path

from lily.utils.errors import ToolError


def _text(name):
    path = Path(name)
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _put(name, text):
    path = Path(name)
    if text is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class Applier:
    def __init__(self, folder):
        self.log = Path(folder) / "last_apply.json"

    def apply(self, items):
        """Write every file. If one fails, put the earlier ones back and raise."""
        done = []   # each file: what it said before and what we wrote
        name = ""
        try:
            for name, content in items.items():
                done.append({"path": name, "old": _text(name), "new": content})
                _put(name, content)
        except (OSError, ValueError) as err:
            self._undo(done, force=True)
            raise ToolError(f"could not save {Path(name).name}: {err}. Nothing was changed.") from err
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text(json.dumps(done), encoding="utf-8")
        return len(done)

    def undo(self):
        """Put back what the last apply replaced. Files edited since are left alone."""
        try:
            done = json.loads(self.log.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ToolError("there is no apply to undo") from None
        skipped = self._undo(done, force=False)
        self.log.unlink(missing_ok=True)
        message = f"Put back {len(done) - len(skipped)} file(s)."
        return message + (f" Left alone, edited since: {', '.join(skipped)}." if skipped else "")

    def _undo(self, done, force):
        skipped = []
        for item in reversed(done):
            name = Path(item["path"]).name
            try:
                if not force and _text(item["path"]) != item["new"]:
                    skipped.append(name)
                    continue
                _put(item["path"], item["old"])
            except (OSError, ValueError):
                skipped.append(name)
        return skipped
