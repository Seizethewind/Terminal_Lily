"""Loads .env, models.toml and the system prompt into one Settings object."""
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from lily.utils.errors import ConfigError
from lily.utils.paths import CONFIG_DIR, DATA_DIR, ROOT


def load_env(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines into os.environ (real env vars win)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        raise ConfigError(f"missing config file: {path}")
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"{path.name}: {err}") from err


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError as err:
        raise ConfigError(f"{name} must be a whole number") from err


@dataclass
class Settings:
    base_url: str
    api_key: str
    profiles: dict
    profile: str
    system_prompt: str
    max_steps: int = 8
    max_history: int = 40
    timeout: int = 60
    rules: dict = field(default_factory=dict)   # profile -> trigger words
    data_dir: Path = DATA_DIR

    @classmethod
    def load(cls, config_dir: Path = CONFIG_DIR) -> "Settings":
        load_env()
        models = _read_toml(config_dir / "models.toml")
        profiles = models.get("profiles") or {}
        default = models.get("default", "auto")
        if default not in profiles:
            raise ConfigError(f"default profile '{default}' is not in models.toml")
        prompt_file = config_dir / "system_prompt.txt"
        prompt = prompt_file.read_text(encoding="utf-8").strip() if prompt_file.is_file() else ""
        return cls(
            base_url=os.environ.get("LILY_BASE_URL", "https://lilyaiapi.onrender.com/v1"),
            api_key=os.environ.get("LILY_API_KEY") or "not_set",   # replace with your key in .env
            profiles=profiles,
            profile=default,
            system_prompt=prompt,
            max_steps=_env_int("LILY_MAX_STEPS", 8),
            timeout=_env_int("LILY_TIMEOUT", 60),
            rules=models.get("rules") or {},
        )
