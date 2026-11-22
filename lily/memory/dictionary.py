"""Your own dictionary: words, what they mean and which taxonomy category they belong to."""
from lily.memory import dict_seed, dict_store
from lily.memory.entity_find import build, find
from lily.memory.taxonomy.paths import clean
from lily.utils.errors import LilyError

MAX_TERM = 60
SHOWN = 5   # meanings added to the prompt for one message
CLIP = 300


def norm(text):
    return " ".join(str(text).lower().split())


class Dictionary:
    def __init__(self, get_db, taxonomy):
        self._get_db, self.tax = get_db, taxonomy

    @property
    def db(self):
        return self._get_db()

    def _path(self, path):
        if not path:
            return ""
        path = self.tax.tree.resolve(clean(path))
        if not self.tax.tree.has(path):
            raise LilyError(f"'{path}' is not in the taxonomy. Find a place with /taxonomy find <word>")
        return path

    def _name(self, text):
        name = norm(text)
        if not 2 <= len(name) <= MAX_TERM or dict_store.SEP in name:
            raise LilyError(f"a word needs 2 to {MAX_TERM} characters and no '{dict_store.SEP}'")
        return name

    def add(self, term, meaning, path=""):
        key, path, meaning = self._name(term), self._path(path), " ".join(meaning.split())
        if not meaning:
            raise LilyError("say what it means: /dict add <word> = <meaning> [@ <category path>]")
        old = dict_store.get(self.db, key)
        dict_store.put(self.db, key, " ".join(term.split()), meaning, path, old["aliases"] if old else [])
        where = f"filed under {path}, run /taxonomy scan to refile older chats" if path else "no category yet"
        return f"saved '{key}' ({where})"

    def alias(self, term, names):
        entry = self._entry(term)
        names = [self._name(name) for name in names.split(",") if name.strip()]
        for name in names:
            other = dict_store.lookup(self.db, name)
            if other and other["term"] != entry["term"]:
                raise LilyError(f"'{name}' already belongs to '{other['term']}'")
        aliases = sorted({*entry["aliases"], *names} - {entry["term"]})
        dict_store.put(self.db, entry["term"], entry["label"], entry["meaning"], entry["path"], aliases)
        return f"'{entry['term']}' is also called: {', '.join(aliases) or 'nothing else'}"

    def _entry(self, word):
        entry = dict_store.lookup(self.db, norm(word))
        if entry is None:
            raise LilyError(f"'{word}' is not in your dictionary. Add it: /dict add {word} = <meaning>")
        return entry

    def show(self, word):
        item = self._entry(word)
        lines = [f"{item['label']}  - {item['meaning']}"]
        lines += [f"  category: {item['path']}"] if item["path"] else []
        return "\n".join(lines + ([f"  also: {', '.join(item['aliases'])}"] if item["aliases"] else []))

    def _list(self, items, empty):
        return "\n".join(f"{item['label']}  - {item['meaning'][:80]}" for item in items) or empty

    def find(self, word):
        return self._list(dict_store.search(self.db, norm(word)), f"nothing in your dictionary mentions '{word}'")

    def under(self, path):
        path = self._path(path)
        return self._list(dict_store.under(self.db, path), f"no words filed under {path}")

    def remove(self, word):
        item = self._entry(word)
        dict_store.remove(self.db, item["term"])
        return f"removed '{item['term']}'"

    def describe(self):
        return f"{len(dict_store.everything(self.db))} word(s) in your dictionary"

    def load(self):
        return dict_seed.load(self)

    def context(self, text):
        """Meanings of your words that a message uses (code is ignored), for the prompt."""
        names = {name: item for item in dict_store.everything(self.db) for name in [item["term"], *item["aliases"]]}
        found = find(build(names), text)
        entries = {names[name]["term"]: names[name] for name in found}.values()
        return [f"[dictionary] {item['label']}: {item['meaning'][:CLIP]}" for item in list(entries)[:SHOWN]]
