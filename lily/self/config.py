"""Reads config/self.toml: the router, workload tiers, roles and limits."""
import os
import shutil
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
    "staging": {"enabled": True},   # writes wait for one apply instead of landing at once
    "autonomy": {"level": "basic"},   # the level on a first start; /auto changes it and it is remembered
}


class SelfConfig:
    def __init__(self, data):
        for key, default in DEFAULTS.items():
            setattr(self, key, {**default, **(data.get(key) or {})})
        self.endpoints = {}   # router name -> url, key, model, timeout; a router without a url is off
        for name in ("lily", "workers", "local"):
            section = data.get(name) or {}
            if section.get("url"):
                env = section.get("key_env")
                key = (os.environ.get(env) or "not_set") if env else ""
                self.endpoints[name] = {"url": section["url"], "key": key,
                                        "model": section.get("model"), "timeout": section.get("timeout")}
        if os.environ.get("LILY_ROUTER", "").lower() == "false":
            self.endpoints.pop("lily", None)
            self.endpoints.pop("workers", None)
        if os.environ.get("LILY_LOCAL", "").lower() == "false" or not shutil.which("ollama"):
            self.endpoints.pop("local", None)   # off by flag, or Ollama is not installed

    @classmethod
    def load(cls, path: Path = CONFIG_DIR / "self.toml"):
        if not path.is_file():
            raise ConfigError(f"missing config file: {path}")
        try:
            return cls(tomllib.loads(path.read_text(encoding="utf-8")))
        except tomllib.TOMLDecodeError as err:
            raise ConfigError(f"{path.name}: {err}") from err
