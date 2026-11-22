"""Loads the starter words in config/dictionary.toml. Words you already have are never changed."""
import tomllib

from lily.memory import dict_store
from lily.utils.errors import ConfigError, LilyError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "dictionary.toml"


def load(book, path=PATH):
    if not path.is_file():
        raise LilyError(f"no starter file at {path.name}")
    try:
        items = tomllib.loads(path.read_text(encoding="utf-8")).get("entry", [])
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f"{path.name}: {err}") from err
    added = kept = skipped = 0
    for item in items:
        key = str(item.get("term", "")).lower()
        if dict_store.lookup(book.db, key):
            kept += 1
            continue
        try:
            book.add(item.get("term", ""), item.get("meaning", ""), item.get("path", ""))
            if item.get("aliases"):
                book.alias(item["term"], ", ".join(item["aliases"]))
            added += 1
        except LilyError:
            skipped += 1
    return f"added {added} word(s), kept {kept} you already had, skipped {skipped}. Run /taxonomy scan to refile chats"
