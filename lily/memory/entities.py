"""The entity taxonomy's word list: 7 classes (entity, location, object, literature, science, math, history)."""
import re
import tomllib
from collections import Counter

from lily.utils.errors import ConfigError, LilyError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "entities.toml"
CLASSES = ("entity", "location", "object", "literature", "science", "math", "history")
SUB = re.compile(r"^[a-z][a-z -]{0,29}$")
NAME = re.compile(r"^\w[\w '-]{0,38}\w$")


def label(text):
    """'Entity/Animal' -> ('entity', 'animal'). A missing subclass becomes 'other'."""
    cls, _, sub = text.lower().strip().partition("/")
    sub = sub.strip() or "other"
    if cls not in CLASSES:
        raise LilyError(f"the class must be one of: {', '.join(CLASSES)} (got '{cls}')")
    if not SUB.match(sub):
        raise LilyError(f"bad subclass '{sub}': use letters only, for example {cls}/animal")
    return cls, sub


def name(text):
    """Tidy a word or phrase: lowercase, single spaces, 2 to 40 characters."""
    word = " ".join(text.lower().split())
    if not NAME.match(word):
        raise LilyError(f"'{text}' is not a usable name (2 to 40 letters or digits)")
    return word


class Taxonomy:
    def __init__(self, path=PATH, extra=()):
        """`extra` is [(word, class, subclass)] you added yourself; those win over the file."""
        data = {}
        if path.is_file():
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as err:
                raise ConfigError(f"{path.name}: {err}") from err
        self.words = {}   # word -> (class, subclass)
        for cls in CLASSES:
            for sub, names in data.get(cls, {}).items():
                for word in names:
                    self.words.setdefault(word.lower().strip(), (cls, sub))
        for word, cls, sub in extra:
            self.words[word] = (cls, sub)

    def describe(self):
        counts = Counter(self.words.values())
        lines = []
        for cls in CLASSES:
            subs = sorted(sub for c, sub in counts if c == cls)
            lines.append(f"{cls:<11} " + (", ".join(f"{sub} ({counts[(cls, sub)]})" for sub in subs) or "-"))
        return "\n".join(lines)
