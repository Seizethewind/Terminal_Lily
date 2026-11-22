"""The category tree: the top levels from config/taxonomy.toml plus the subcategories you add."""
from lily.memory.taxonomy import parts
from lily.memory.taxonomy.paths import clean, is_unknown, parent
from lily.utils.errors import ConfigError, LilyError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "taxonomy.toml"


def _within(path, top):
    return path == top or path.startswith(top + "/")


def load_config(path=PATH):
    """Read the file. Returns (roots, subs, legacy, alias, inside): each a {path: text-or-path} dict."""
    data = parts.load(path)
    try:
        roots = {clean(key): str(text) for key, text in data.get("roots", {}).items()}
        subs = {clean(key): str(text) for key, text in data.get("sub", {}).items()}
        legacy = {key.lower(): clean(value) for key, value in data.get("legacy", {}).items()}
        alias, inside = ({clean(old): clean(new) for old, new in data.get(name, {}).items()}
                         for name in ("alias", "inside"))
    except LilyError as err:
        raise ConfigError(f"{path.name}: {err}") from err
    if any("/" in root or is_unknown(root) for root in roots):
        raise ConfigError(f"{path.name}: [roots] needs single words, and 'unknown' is reserved")
    return roots, subs, legacy, alias, inside


class Tree:
    def __init__(self, config, extra=()):
        """`extra` is [(path, text)] added at run time (/taxonomy add, or the legacy bridge)."""
        roots, subs, self.legacy, *moves = config
        self.alias, self.inside = moves or ({}, {})   # older id -> new id / older id -> broader branch
        self.roots = tuple(roots)
        self.nodes = dict(roots)   # path -> description
        for path in sorted(subs, key=lambda item: item.count("/")):
            if parent(path) not in self.nodes:
                raise ConfigError(f"taxonomy.toml: '{path}' needs '{parent(path)}' to exist first")
            self.nodes[path] = subs[path]
        for old, new in self.moved.items():
            if old in self.nodes or new not in self.nodes:
                raise ConfigError(f"taxonomy.toml: '{old}' = '{new}' must name a branch that is not itself an older name")
        for path, text in extra:
            self.nodes.setdefault(path, text)

    @property
    def moved(self):
        return {**self.alias, **self.inside}

    def has(self, path):
        return path in self.nodes or is_unknown(path)

    def resolve(self, path):
        """The current id of a path: an alias becomes its new branch."""
        return self.alias.get(path, path)

    def names(self, path):
        """A branch under its new id and every older id that means the same thing."""
        new = self.resolve(path)
        return [new, *(old for old, target in self.alias.items() if target == new)]

    def is_old(self, path):
        return any(_within(path, old) for old in self.moved)

    def span(self, path):
        """What else counts as `path`: (older paths filed under it, older paths below it that belong
        elsewhere, older ids with the same meaning)."""
        also = [old for old, new in self.moved.items() if _within(new, path) and not _within(old, path)]
        skip = [old for old, new in self.moved.items() if old.startswith(path + "/") and not _within(new, path)]
        return also, skip, [old for old, new in self.alias.items() if new == path]

    def check_new(self, path):
        """The cleaned path of a subcategory you may add, or an explanation why not."""
        path = clean(path)
        if "/" not in path or is_unknown(path):
            raise LilyError(f"'{path}' is not a subcategory. New top-level categories are set in "
                            f"config/taxonomy.toml; the current ones are: {', '.join(self.roots)}")
        if path in self.alias:
            raise LilyError(f"'{path}' is an older id of '{self.alias[path]}'. Use that one")
        if parent(path) not in self.nodes:
            raise LilyError(f"'{parent(path)}' does not exist yet, so '{path}' has no place to go")
        if path in self.nodes:
            raise LilyError(f"'{path}' already exists")
        return path

    def children(self, path=""):
        return sorted(item for item in self.nodes if parent(item) == path)

    def shown(self, path):
        """Children as the report draws them: renamed ones are folded away, nested ones sit under their new home."""
        own = [item for item in self.children(path) if item not in self.moved]
        return own + sorted(old for old, new in self.inside.items() if new == path and old in self.nodes)

    def walk(self):
        """[(path, depth)] top to bottom: roots in file order, children alphabetically."""
        order = []

        def visit(path, depth):
            order.append((path, depth))
            for child in self.shown(path):
                visit(child, depth + 1)

        for root in self.roots:
            visit(root, 0)
        return order
