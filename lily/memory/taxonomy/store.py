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


def refs(db, path, kind=None):
    """[(kind, ref)] of the records labelled at `path` or anywhere below it."""
    sql = "SELECT DISTINCT kind, ref FROM taxonomy_labels WHERE (path = ? OR path LIKE ?)"
    params = [path, path + "/%"]
    if kind:
        sql, params = sql + " AND kind = ?", [*params, kind]
    return db.rows(sql + " ORDER BY kind, ref", params)


def labelled_refs(db, kind):
    return {ref for (ref,) in db.rows("SELECT DISTINCT ref FROM taxonomy_labels WHERE kind = ?", (kind,))}


def count(db, path):
    """Records at or below `path`, and records labelled exactly at it."""
    deep = db.rows("SELECT count(DISTINCT kind || ':' || ref) FROM taxonomy_labels "
                   "WHERE path = ? OR path LIKE ?", (path, path + "/%"))[0][0]
    here = db.rows("SELECT count(*) FROM taxonomy_labels WHERE path = ?", (path,))[0][0]
    return deep, here


def label_paths(db):
    """[(path, labels)] for every path in use."""
    return db.rows("SELECT path, count(*) FROM taxonomy_labels GROUP BY path ORDER BY path")
