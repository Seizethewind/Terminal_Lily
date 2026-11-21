"""Named model roles: which tier (light, normal or heavy) each job uses. A change is remembered."""
import json
import re
from pathlib import Path

from lily.utils.errors import LilyError

TIERS = ("light", "normal", "heavy")
JOBS = {   # the jobs Lily knows about
    "planner": "splits a big task into steps",
    "namer": "gives each task a short title",
    "summarizer": "writes the summary of earlier chats",
    "coder": "workers that write or change code",
    "researcher": "workers that look things up",
    "takeover": "Lily finishing what a worker could not",
}
NAME = re.compile(r"^[a-z][a-z0-9_-]{0,23}$")


class Roles:
    def __init__(self, cfg, folder):
        self.cfg, self.file = cfg, Path(folder) / "roles.json"
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.saved = {r: t for r, t in saved.items() if t in TIERS and NAME.match(str(r))} if isinstance(saved, dict) else {}
        cfg.roles.update(self.saved)   # what you set with /roles beats config/self.toml

    def set(self, role, tier):
        role = role.lower()
        if tier not in TIERS:
            raise LilyError(f"unknown tier '{tier}'. Options: {', '.join(TIERS)}")
        if role != "default" and not NAME.match(role):
            raise LilyError("a role is a short name: letters, digits, - or _")
        self.cfg.roles[role] = self.saved[role] = tier
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.saved), encoding="utf-8")

    def describe(self, models):
        names = [*JOBS, *sorted(role for role in self.cfg.roles if role not in JOBS and role != "default")]
        names.append("default")
        lines = []
        for role in names:
            tier = self.cfg.roles.get(role, self.cfg.roles["default"])
            what = JOBS.get(role, "any role nobody named" if role == "default" else "your own role")
            lines.append(f"{role:<11} {tier:<6} {models.model(tier) if tier in TIERS else '?':<10} {what}")
        return "\n".join(["Model roles (change with /roles <role> <light|normal|heavy>):", *lines])
