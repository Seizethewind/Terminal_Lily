"""Reads config/mcp_servers.toml."""
import os
import tomllib

from lily.utils.errors import ConfigError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "mcp_servers.toml"


def load_servers(path=PATH):
    """Return the enabled servers as dicts: name, url, auth_env, token."""
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"{path.name}: {err}") from err
    servers = []
    for entry in data.get("servers", []):
        if not entry.get("enabled", True):
            continue
        if not entry.get("name") or not entry.get("url"):
            raise ConfigError(f"{path.name}: every server needs a name and a url")
        env = entry.get("auth_env", "")
        token = os.environ.get(env, "") if env else ""
        servers.append({"name": entry["name"], "url": entry["url"], "auth_env": env, "token": token})
    return servers
