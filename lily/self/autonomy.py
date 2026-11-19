"""How much Lily may do without asking: none, basic, semi or full. Remembered between sessions."""
import json
from pathlib import Path

from lily.utils.errors import LilyError

LEVELS = {
    "none": "asks before every tool",
    "basic": "looks around freely; saving and other changes ask (the default)",
    "semi": "basic, and saves or undoes staged files without asking",
    "full": "semi, and runs ordinary commands in the workplace without asking",
}


class Autonomy:
    def __init__(self, folder, default="basic"):
        self.file = Path(folder) / "autonomy.json"
        self.level = self._load(default if default in LEVELS else "basic")

    def _load(self, default):
        try:
            level = json.loads(self.file.read_text(encoding="utf-8")).get("level")
        except (OSError, ValueError, AttributeError):
            return default
        return level if level in LEVELS else default

    def set(self, level):
        if level not in LEVELS:
            raise LilyError(f"unknown level '{level}'. Options: {', '.join(LEVELS)}")
        self.level = level
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps({"level": level}), encoding="utf-8")

    def describe(self):
        lines = [f"{'*' if name == self.level else ' '} {name:<6} {text}" for name, text in LEVELS.items()]
        return "\n".join(["Autonomy (change with /auto <level>):", *lines])
