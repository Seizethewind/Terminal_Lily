"""Reads and writes the dictionary table: your words, what they mean and where they belong."""
from lily.memory.db import now

SEP = "|"   # aliases are stored joined by this
COLUMNS = "term, label, meaning, path, aliases"


def put(db, term, label, meaning, path, aliases):
    db.write(f"INSERT OR REPLACE INTO dictionary({COLUMNS}, ts) VALUES (?, ?, ?, ?, ?, ?)",
             (term, label, meaning, path, SEP.join(aliases), now()))


def _entry(row):
    return {"term": row[0], "label": row[1], "meaning": row[2], "path": row[3],
            "aliases": [alias for alias in row[4].split(SEP) if alias]}


def get(db, term):
    rows = db.rows(f"SELECT {COLUMNS} FROM dictionary WHERE term = ?", (term,))
    return _entry(rows[0]) if rows else None


def everything(db):
    return [_entry(row) for row in db.rows(f"SELECT {COLUMNS} FROM dictionary ORDER BY term")]


def lookup(db, word):
    """The entry whose term or alias is this word, or None."""
    return next((item for item in everything(db) if word == item["term"] or word in item["aliases"]), None)


def remove(db, term):
    db.write("DELETE FROM dictionary WHERE term = ?", (term,))


def search(db, word):
    return [item for item in everything(db)
            if word in item["term"] or word in item["meaning"].lower() or any(word in a for a in item["aliases"])]


def under(db, path):
    return [item for item in everything(db) if item["path"] == path or item["path"].startswith(path + "/")]


def phrases(db):
    """{lowercase term or alias: category path} for the entries that have a category."""
    return {name: item["path"] for item in everything(db) if item["path"]
            for name in [item["term"], *item["aliases"]]}
