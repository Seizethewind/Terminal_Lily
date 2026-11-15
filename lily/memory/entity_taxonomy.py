"""The entity taxonomy in use: finds the known words in your chats and files them as class > subclass."""
from collections import Counter

from lily.memory import entity_store
from lily.memory.entities import CLASSES, Taxonomy, label, name
from lily.memory.entity_find import build, find as find_words
from lily.utils.errors import LilyError

SHOWN = 6   # words listed per subclass in the report


class EntityTaxonomy:
    def __init__(self, get_db, taxonomy=None):
        self._get_db = get_db
        self._tax = taxonomy
        self._pattern = build(taxonomy.words) if taxonomy is not None else None

    @property
    def tax(self):
        """Loaded on first use; your own words (/entity add) are merged in."""
        if self._tax is None:
            self._tax = Taxonomy(extra=entity_store.terms(self._get_db()))
            self._pattern = build(self._tax.words)
        return self._tax

    def index_run(self, run_id, user_text, answer):
        """File the words of one chat. Returns how many different words were found."""
        words = self.tax.words
        found = Counter()
        for text in (user_text, answer):
            found.update(find_words(self._pattern, text))
        entity_store.save(self._get_db(), run_id, found, words)
        return len(found)

    def scan(self):
        """Re-file every stored chat (after editing config/entities.toml or adding words)."""
        self._tax = None
        runs = self._get_db().rows("SELECT id, user_text, answer FROM runs ORDER BY id")
        total = sum(self.index_run(*run) for run in runs)
        return f"scanned {len(runs)} chat(s), found {total} word(s) from the taxonomy"

    def classes(self):
        return self.tax.describe()

    def report(self):
        rows = entity_store.summary(self._get_db())
        if not rows:
            return "nothing filed yet. Mention things in a chat (a dog, a city...), or run /entity scan"
        tree = {}
        for cls, sub, word, total, _ in rows:
            tree.setdefault(cls, {}).setdefault(sub, []).append(f"{word} x{total}")
        lines = []
        for cls in CLASSES:
            lines += [cls] if cls in tree else []
            for sub, items in tree.get(cls, {}).items():
                lines.append(f"  {sub}: {', '.join(items[:SHOWN])}" + (" ..." if len(items) > SHOWN else ""))
        return "\n".join(lines)

    def show(self, text):
        """The words filed under a class ('object') or a subclass ('object/device')."""
        cls, sub = label(text) if "/" in text else (text.lower(), "")
        if cls not in CLASSES:
            raise LilyError(f"the class must be one of: {', '.join(CLASSES)} (got '{cls}')")
        rows = [r for r in entity_store.summary(self._get_db()) if r[0] == cls and sub in ("", r[1])]
        if not rows:
            return f"nothing filed under {text} yet"
        return "\n".join(f"{total:>4}x {word}  [{s}]  in {chats} chat(s)" for _, s, word, total, chats in rows)

    def find(self, text):
        """The latest chats that mention a word."""
        word = name(text)
        rows = entity_store.chats(self._get_db(), word)
        first = lambda line: " ".join((line or "").split())[:70]   # noqa: E731
        return "\n".join(f"chat #{run}: {first(question)}" for run, question in rows) or f"no chat mentions '{word}'"

    def add(self, text, kind):
        word, (cls, sub) = name(text), label(kind)
        entity_store.add_term(self._get_db(), word, cls, sub)
        self._tax = None
        return f"added '{word}' as {cls} > {sub}. Run /entity scan to apply it to older chats"

    def remove(self, text):
        word = name(text)
        if word not in {row[0] for row in entity_store.terms(self._get_db())}:
            raise LilyError(f"'{word}' is not one you added. Words from config/entities.toml are removed by editing it")
        entity_store.remove_term(self._get_db(), word)
        self._tax = None
        return f"removed '{word}'. Run /entity scan to refresh older chats"
