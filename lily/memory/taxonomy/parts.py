"""Reads config/taxonomy.toml and merges every *.toml file in config/taxonomy.d/ into it."""
import tomllib

from lily.utils.errors import ConfigError


def _read(path):
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"{path.name}: {err}") from err


def load(path):
    """The file as a dict. For the main file, the extra files add to its sections (no key twice)."""
    data = _read(path) if path.is_file() else {}
    if path.name != "taxonomy.toml":
        return data
    for extra in sorted((path.parent / "taxonomy.d").glob("*.toml")):
        for section, items in _read(extra).items():
            mine = data.setdefault(section, {})
            for key in items:
                if key in mine:
                    raise ConfigError(f"{extra.name}: '{key}' is already defined")
            mine.update(items)
    return data
