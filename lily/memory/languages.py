"""The language list (config/languages.toml) and the naming of code-block tags."""
import re
import tomllib

from lily.utils.errors import ConfigError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "languages.toml"
GROUPS = ("programming", "shell", "query", "markup", "data", "config")
SAFE = re.compile(r"^[a-z0-9+#._-]{1,30}$")


def clean(tag):
    """'```{.Python}' -> 'python'. Returns '' if nothing usable is left."""
    tag = tag.strip().lower().strip("{}").lstrip(".")
    for prefix in ("language-", "lang-"):
        tag = tag.removeprefix(prefix)
    return tag if SAFE.match(tag) else ""


class Languages:
    def __init__(self, path=PATH):
        data = {}
        if path.is_file():
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as err:
                raise ConfigError(f"{path.name}: {err}") from err
        self.ignore = {tag.lower() for tag in data.get("ignore", [])}
        self.info, self.alias = {}, {}
        for name, entry in data.get("languages", {}).items():
            self.info[name] = (entry.get("group", "programming"), entry.get("family", ""))
            self.alias[name] = name
            for alias in entry.get("aliases", []):
                self.alias[alias.lower()] = name

    def resolve(self, tag):
        """None if the tag is not code. Otherwise language, group, family and known.

        A tag that is not in the list is kept as its own language (known = False).
        """
        tag = clean(tag)
        if not tag or tag in self.ignore:
            return None
        name = self.alias.get(tag)
        if name is None:
            return {"language": tag, "group": "unknown", "family": "", "known": False}
        group, family = self.info[name]
        return {"language": name, "group": group, "family": family, "known": True}
