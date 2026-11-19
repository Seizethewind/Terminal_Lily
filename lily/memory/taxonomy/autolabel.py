"""Files a chat under the categories it names: "optics" -> study/science/physics/optics."""
import tomllib
from collections import Counter

from lily.memory.entity_find import build, find
from lily.memory.taxonomy import store
from lily.utils.errors import ConfigError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "taxonomy_auto.toml"
SOURCE = "auto:tree"   # labels made here carry this source, so a rescan only replaces these
MIN_DEPTH = 2   # areas and topics. Branches like study/history are too broad to match by name
NEEDED = 2   # your message counts 2, her answer 1


def load_settings(path=PATH):
    """(names to skip, {extra word: path}, most labels per chat)."""
    data = {}
    if path.is_file():
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as err:
            raise ConfigError(f"{path.name}: {err}") from err
    limit = data.get("max_labels", 6)
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ConfigError(f"{path.name}: max_labels must be a number from 1 to 20")
    return {str(name) for name in data.get("skip", [])}, {str(k).lower(): str(v) for k, v in data.get("words", {}).items()}, limit


class Matcher:
    def __init__(self, tree, settings=None):
        skip, words, self.limit = settings or load_settings()
        self.phrases = {}   # lowercase word or phrase -> the paths it points at
        for path in tree.nodes:
            name = path.rpartition("/")[2]
            if path.count("/") >= MIN_DEPTH and name not in skip:
                self.phrases.setdefault(name.replace("-", " "), set()).add(path)
        for word, path in words.items():
            if path in tree.nodes:
                self.phrases.setdefault(word, set()).add(path)
        self.pattern = build(self.phrases)

    def paths(self, user_text, answer):
        """The categories a chat names, most specific only, at most `limit`."""
        score = Counter()
        for weight, text in ((2, user_text), (1, answer)):
            for phrase, count in find(self.pattern, text).items():
                for path in self.phrases[phrase]:
                    score[path] += weight * count
        found = [path for path, points in score.items() if points >= NEEDED]
        found = [path for path in found if not any(other.startswith(path + "/") for other in found)]
        return sorted(found, key=lambda path: (-score[path], path))[:self.limit]


def label_run(tax, run_id, user_text="", answer="", matcher=None):
    """Replace the automatic labels of this kind on one chat. Your own labels are never touched."""
    ref = str(run_id)
    matcher = matcher or Matcher(tax.tree, tax.auto)
    store.unlabel(tax.db, "run", ref, source=SOURCE)
    paths = matcher.paths(user_text, answer)
    for path in paths:
        tax.classify("run", ref, path, SOURCE)
    return len(paths)
