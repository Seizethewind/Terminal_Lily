"""Reads and writes the taxonomy tables. Labels only point at records; they never change them."""
from lily.memory.db import now


def nodes(db):
    """[(path, description)] the subcategories added at run time."""
    return db.rows("SELECT path, description FROM taxonomy_nodes ORDER BY path")


def add_node(db, path, description=""):
    db.write("INSERT OR REPLACE INTO taxonomy_nodes(path, description, ts) VALUES (?, ?, ?)",
             (path, description, now()))


def remove_node(db, path):
    db.write("DELETE FROM taxonomy_nodes WHERE path = ?", (path,))


def label(db, kind, ref, path, source):
    """Give a record a category. Your own labels replace an automatic one on the same path."""
    if source == "user":
        db.write("DELETE FROM taxonomy_labels WHERE kind = ? AND ref = ? AND path = ?", (kind, ref, path))
    db.write("INSERT OR IGNORE INTO taxonomy_labels(kind, ref, path, source, ts) VALUES (?, ?, ?, ?, ?)",
             (kind, ref, path, source, now()))


def unlabel(db, kind, ref, path=None, source=None):
    """Remove labels of one record (all, one path, or one source). Returns how many."""
    where, params = "kind = ? AND ref = ?", [kind, ref]
    for column, value in (("path", path), ("source", source)):
        if value:
            where, params = f"{where} AND {column} = ?", [*params, value]
    count = db.rows(f"SELECT count(*) FROM taxonomy_labels WHERE {where}", params)[0][0]
    db.write(f"DELETE FROM taxonomy_labels WHERE {where}", params)
    return count


def labels_of(db, kind, ref):
    """[(path, source)] of one record."""
    return db.rows("SELECT path, source FROM taxonomy_labels WHERE kind = ? AND ref = ? ORDER BY path",
                   (kind, ref))


NO_SPAN = ((), (), ())   # what Tree.span() returns when no older ids are involved


def _within(path, span):
    """SQL for 'at or below path', adjusted for older ids (see Tree.span)."""
    also, skip, _ = span
    sql, params = "(path = ? OR path LIKE ?)", [path, path + "/%"]
    for old in skip:
        sql, params = sql + " AND NOT (path = ? OR path LIKE ?)", [*params, old, old + "/%"]
    sql = f"({sql})"
    for old in also:
        sql, params = sql + " OR (path = ? OR path LIKE ?)", [*params, old, old + "/%"]
    return f"({sql})", params


def refs(db, path, kind=None, span=NO_SPAN):
    """[(kind, ref)] of the records labelled at `path` or anywhere below it."""
    where, params = _within(path, span)
    sql = f"SELECT DISTINCT kind, ref FROM taxonomy_labels WHERE {where}"
    if kind:
        sql, params = sql + " AND kind = ?", [*params, kind]
    return db.rows(sql + " ORDER BY kind, ref", params)


def labelled_refs(db, kind):
    return {ref for (ref,) in db.rows("SELECT DISTINCT ref FROM taxonomy_labels WHERE kind = ?", (kind,))}


def count(db, path, span=NO_SPAN):
    """Records at or below `path`, and labels exactly at it (or at an older id of it)."""
    where, params = _within(path, span)
    deep = db.rows(f"SELECT count(DISTINCT kind || ':' || ref) FROM taxonomy_labels WHERE {where}", params)[0][0]
    exact = [path, *span[2]]
    here = db.rows(f"SELECT count(*) FROM taxonomy_labels WHERE path IN ({','.join('?' * len(exact))})", exact)[0][0]
    return deep, here


def label_paths(db):
    """[(path, labels)] for every path in use."""
    return db.rows("SELECT path, count(*) FROM taxonomy_labels GROUP BY path ORDER BY path")
