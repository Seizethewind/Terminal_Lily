"""The universal data taxonomy: label any stored record with one or more categories."""
import re

from lily.memory.taxonomy import legacy, report, store
from lily.memory.taxonomy.paths import ancestors, clean
from lily.memory.taxonomy.tree import Tree, load_config
from lily.utils.errors import LilyError

KIND = re.compile(r"^[a-z][a-z0-9_-]{0,19}$")
MAX_REF = 300
PREVIEW = 60   # characters of a chat shown when listing unclassified runs


class Taxonomy:
    def __init__(self, get_db, sources=lambda: (), config=None):
        """`sources` lists the note sources (from RAG). `config` is load_config()'s result (for tests)."""
        self._get_db, self._config, self._tree = get_db, config, None
        # A kind of record is a name plus a function that lists its records as [(ref, preview)].
        # Anything can be labelled without being listed here; listing only powers "unclassified".
        self.kinds = {"run": self._runs, "note": lambda: [(source, "") for source in sources()]}

    @property
    def db(self):
        return self._get_db()

    @property
    def tree(self):
        if self._tree is None:
            self._tree = Tree(self._config or load_config(), store.nodes(self.db))
        return self._tree

    def _runs(self):
        rows = self.db.rows("SELECT id, substr(replace(user_text, char(10), ' '), 1, ?) FROM runs ORDER BY id",
                            (PREVIEW,))
        return [(str(run), text) for run, text in rows]

    def add(self, path, description=""):
        path = self.tree.check_new(path)
        store.add_node(self.db, path, description)
        self._tree = None
        return f"added {path}"

    def remove(self, path):
        path = clean(path)
        if path not in {item for item, _ in store.nodes(self.db)}:
            raise LilyError(f"only categories you added can be removed. Edit config/taxonomy.toml for '{path}'")
        if self.tree.children(path) or store.count(self.db, path)[0]:
            raise LilyError(f"'{path}' still has subcategories or records. Move or unlabel them first")
        store.remove_node(self.db, path)
        self._tree = None
        return f"removed {path}"

    def _ensure(self, path):
        for part in [*ancestors(path), path]:
            if part not in self.tree.nodes:
                store.add_node(self.db, self.tree.check_new(part))
                self._tree = None

    def classify(self, kind, ref, path, source="user", create=False):
        """Add one category to a record. A record can have many. `create` registers missing subcategories."""
        kind, ref, path = self._kind(kind), self._ref(ref), clean(path)
        if not self.tree.has(path):
            if not create:
                raise LilyError(f"'{path}' is not in the taxonomy yet. Add it first: /taxonomy add {path}")
            self._ensure(path)
        store.label(self.db, kind, ref, path, source)
        return f"{kind} {ref}: {path}"

    def unclassify(self, kind, ref, path=None):
        removed = store.unlabel(self.db, self._kind(kind), self._ref(ref), clean(path) if path else None)
        return f"removed {removed} label(s)"

    def of(self, kind, ref):
        rows = store.labels_of(self.db, self._kind(kind), self._ref(ref))
        return "\n".join(f"{path}  ({source})" for path, source in rows) or "no labels: it is unclassified"

    def refs(self, paths, kind=None, mode="any"):
        """[(kind, ref)] labelled at or below the paths: any of them, or all of them."""
        if not paths:
            raise LilyError("give at least one category path")
        found = [set(store.refs(self.db, clean(path), kind)) for path in paths]
        return sorted(set.intersection(*found) if mode == "all" else set.union(*found))

    def unclassified(self, kind):
        """[(ref, preview)] of the records of this kind that have no label yet."""
        if kind not in self.kinds:
            raise LilyError(f"cannot list '{kind}' records. Kinds that can be listed: {', '.join(self.kinds)}")
        done = store.labelled_refs(self.db, kind)
        return [(ref, text) for ref, text in self.kinds[kind]() if ref not in done]

    def index_run(self, run_id, user_text="", answer=""):
        """Called after every chat: label it from what the older taxonomies found."""
        return legacy.label_run(self, run_id)

    def scan(self):
        runs = [row[0] for row in self.db.rows("SELECT id FROM runs ORDER BY id")]
        total = sum(legacy.label_run(self, run) for run in runs)
        return f"scanned {len(runs)} chat(s), made {total} automatic label(s)"

    def report(self):
        return report.render(self.tree, self.db, {kind: self.unclassified(kind) for kind in self.kinds})

    @staticmethod
    def _kind(kind):
        kind = str(kind).strip().lower()
        if not KIND.match(kind):
            raise LilyError(f"'{kind}' is not a kind of record (use a short lowercase word, like run or note)")
        return kind

    @staticmethod
    def _ref(ref):
        ref = str(ref).strip()
        if not ref or len(ref) > MAX_REF:
            raise LilyError(f"a record reference must be 1 to {MAX_REF} characters")
        return ref
