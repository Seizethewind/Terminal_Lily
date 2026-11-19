"""Files Lily wants to write wait here, outside the project, until the user applies them."""
import json
import threading
from pathlib import Path


class StageStore:
    def __init__(self, folder):
        self.file = Path(folder) / "pending.json"
        self.lock = threading.Lock()
        self.pending = self._load()   # full path -> the complete new text

    def _load(self):
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.pending), encoding="utf-8")

    def text(self, path):
        """What the file says now: the waiting version, else the one on disk, else nothing."""
        name = str(path)
        if name in self.pending:
            return self.pending[name]
        try:
            return Path(name).read_text(encoding="utf-8")
        except (OSError, ValueError):
            return ""

    def stage(self, path, content, append=False):
        with self.lock:
            self.pending[str(path)] = (self.text(path) + content) if append else content
            self._save()

    def get(self, path):
        return self.pending.get(str(path))

    def snapshot(self):
        with self.lock:
            return dict(self.pending)

    def drop(self, path=None):
        """Forget one waiting file, or all of them. Returns how many were dropped."""
        with self.lock:
            names = list(self.pending) if path is None else [str(path)]
            count = sum(1 for name in names if self.pending.pop(name, None) is not None)
            self._save()
        return count

    def take_all(self):
        with self.lock:
            items, self.pending = self.pending, {}
            self._save()
        return items

    def put_back(self, items):
        """Return files after a failed apply, without overwriting anything staged since."""
        with self.lock:
            for name, content in items.items():
                self.pending.setdefault(name, content)
            self._save()
