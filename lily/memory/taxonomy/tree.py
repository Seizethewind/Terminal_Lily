"""The category tree: the top levels from config/taxonomy.toml plus the subcategories you add."""
import tomllib

from lily.memory.taxonomy.paths import clean, is_unknown, parent
from lily.utils.errors import ConfigError, LilyError
from lily.utils.paths import CONFIG_DIR

PATH = CONFIG_DIR / "taxonomy.toml"


def load_config(path=PATH):
    """Read the file. Returns (roots, subs, legacy): {path: text}, {path: text}, {key: path}."""
    data = {}
    if path.is_file():
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as err:
            raise ConfigError(f"{path.name}: {err}") from err
    try:
        roots = {clean(key): str(text) for key, text in data.get("roots", {}).items()}
        subs = {clean(key): str(text) for key, text in data.get("sub", {}).items()}
        legacy = {key.lower(): clean(value) for key, value in data.get("legacy", {}).items()}
    except LilyError as err:
        raise ConfigError(f"{path.name}: {err}") from err
    if any("/" in root or is_unknown(root) for root in roots):
        raise ConfigError(f"{path.name}: [roots] needs single words, and 'unknown' is reserved")
    return roots, subs, legacy


class Tree:
    def __init__(self, config, extra=()):
        """`extra` is [(path, text)] added at run time (/taxonomy add, or the legacy bridge)."""
        roots, subs, self.legacy = config
        self.roots = tuple(roots)
        self.nodes = dict(roots)   # path -> description
        for path in sorted(subs, key=lambda item: item.count("/")):
            if parent(path) not in self.nodes:
                raise ConfigError(f"taxonomy.toml: '{path}' needs '{parent(path)}' to exist first")
            self.nodes[path] = subs[path]
        for path, text in extra:
            self.nodes.setdefault(path, text)

    def has(self, path):
        return path in self.nodes or is_unknown(path)

    def check_new(self, path):
        """The cleaned path of a subcategory you may add, or an explanation why not."""
        path = clean(path)
        if "/" not in path or is_unknown(path):
            raise LilyError(f"'{path}' is not a subcategory. New top-level categories are set in "
                            f"config/taxonomy.toml; the current ones are: {', '.join(self.roots)}")
        if parent(path) not in self.nodes:
            raise LilyError(f"'{parent(path)}' does not exist yet, so '{path}' has no place to go")
        if path in self.nodes:
            raise LilyError(f"'{path}' already exists")
        return path

    def children(self, path=""):
        return sorted(item for item in self.nodes if parent(item) == path)

    def walk(self):
        """[(path, depth)] top to bottom: roots in file order, children alphabetically."""
        order = []

        def visit(path, depth):
            order.append((path, depth))
            for child in self.children(path):
                visit(child, depth + 1)

        for root in self.roots:
            visit(root, 0)
        return order
