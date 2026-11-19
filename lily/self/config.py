"""Reads config/self.toml: the two routers, workload tiers, roles and limits."""
import os
import tomllib
from pathlib import Path

from lily.utils.errors import ConfigError
from lily.utils.paths import CONFIG_DIR

DEFAULTS = {
    "tiers": {"light": "auto:fast", "normal": "auto", "heavy": "auto:smart"},
    "roles": {"default": "normal"},
    "limits": {"max_workers": 3, "worker_steps": 6, "approval_wait": 120, "breaker_fails": 3,
               "breaker_pause": 60, "recent_turns": 6, "timeout": 60},
    "personality": {"text": ""},
}


class SelfConfig:
    def __init__(self, data):
        for key, default in DEFAULTS.items():
            setattr(self, key, {**default, **(data.get(key) or {})})
        self.endpoints = {}   # router name -> {"url", "key"}; a router without a url is off
        for name in ("lily", "workers"):
            section = data.get(name) or {}
            if section.get("url"):
                key = os.environ.get(section.get("key_env", "")) or "not_set"
                self.endpoints[name] = {"url": section["url"], "key": key}

    @classmethod
    def load(cls, path: Path = CONFIG_DIR / "self.toml"):
        if not path.is_file():
            raise ConfigError(f"missing config file: {path}")
        try:
            return cls(tomllib.loads(path.read_text(encoding="utf-8")))
        except tomllib.TOMLDecodeError as err:
            raise ConfigError(f"{path.name}: {err}") from err
