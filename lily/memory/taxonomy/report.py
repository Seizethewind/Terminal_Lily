"""Plain-text views of the taxonomy."""
from lily.memory.taxonomy import store
from lily.memory.taxonomy.paths import UNKNOWN, is_unknown

SHORT = 60   # characters of a description that are shown


def render(tree, db, unclassified):   # unclassified = {kind: how many have no label}
    """The tree with record counts, then unknown, stray paths and unclassified totals."""
    lines, shown = [], set()
    for path, depth in tree.walk():
        shown.add(path)
        deep, here = store.count(db, path, tree.span(path))
        counts = f"  {deep} record(s)" + (f", {here} here" if deep != here and here else "") if deep else ""
        text = tree.nodes[path][:SHORT]
        lines.append(f"{'  ' * depth}{path.rpartition('/')[2]}{counts}" + (f"  - {text}" if text else ""))
    unknown = 0
    for path, labels in store.label_paths(db):
        if is_unknown(path):
            unknown += labels
        elif path not in shown and not tree.is_old(path):
            lines.append(f"{path}  {labels} label(s)  - not in the tree (was the config edited?)")
    if unknown:
        lines.append(f"{UNKNOWN}  {store.count(db, UNKNOWN)[0]} record(s)  - looked at, does not fit yet")
    pending = [f"{kind} {count}" for kind, count in unclassified.items() if count]
    lines.append("unclassified  " + (", ".join(pending) if pending else "nothing"))
    return "\n".join(lines)
