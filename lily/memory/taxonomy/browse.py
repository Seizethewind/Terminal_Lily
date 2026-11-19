"""Looking things up in the tree: what a branch means, what is inside it, where a word belongs."""
import re

from lily.memory.taxonomy import store
from lily.memory.taxonomy.paths import clean
from lily.utils.errors import LilyError

SHORT = 70   # characters of a definition shown in a list
LIMIT = 15   # most results of a search


def about(tree, db, path):
    """A branch's definition, its older ids, and what is directly inside it."""
    path = tree.resolve(clean(path))
    if path not in tree.nodes:
        raise LilyError(f"'{path}' is not in the taxonomy. Find where a word belongs with /taxonomy find <word>")
    lines = [f"{path}  - {tree.nodes[path]}"]
    older = tree.names(path)[1:]
    if older:
        lines.append(f"older ids: {', '.join(older)}")
    for child in tree.shown(path):
        deep, _ = store.count(db, child, tree.span(child))
        lines.append(f"  {child.rpartition('/')[2]}" + (f"  {deep} record(s)" if deep else "")
                     + f"  - {tree.nodes.get(child, '')[:SHORT]}")
    return "\n".join(lines if len(lines) > 1 else [*lines, "  (nothing inside yet)"])


def find(tree, word):
    """Categories whose name or definition has the word; name matches come first."""
    word = word.lower().strip()
    if len(word) < 2:
        raise LilyError("give a word of at least 2 letters, for example /taxonomy find optics")
    pattern = re.compile(rf"(?<!\w){re.escape(word)}", re.I)
    hits = []
    for path, text in tree.nodes.items():
        if "/" in path and (pattern.search(path.rpartition("/")[2].replace("-", " ")) or pattern.search(text)):
            named = bool(pattern.search(path.rpartition("/")[2].replace("-", " ")))
            hits.append((not named, path.count("/"), path, text))
    hits.sort()
    lines = [f"{path}  - {text[:SHORT]}" for _, _, path, text in hits[:LIMIT]]
    if len(hits) > LIMIT:
        lines.append(f"... and {len(hits) - LIMIT} more. Try a more exact word")
    return "\n".join(lines) or f"nothing in the taxonomy mentions '{word}'. Add a place for it with /taxonomy add"
