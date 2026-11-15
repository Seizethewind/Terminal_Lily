"""The SQLite full-text store (FTS5). Nothing else in Lily touches the database."""
import sqlite3
from pathlib import Path

from lily.utils.errors import LilyError

SCHEMA = "CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(source, body, tokenize='porter unicode61')"


class Store:
    def __init__(self, path):
        try:
            if str(path) != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(path))
            self.db.execute(SCHEMA)
        except (sqlite3.Error, OSError) as err:
            raise LilyError(f"cannot open the notes database: {err}") from err

    def _query(self, sql, params=()):
        try:
            with self.db:   # commits on success, rolls back on error
                return self.db.execute(sql, params).fetchall()
        except sqlite3.Error as err:
            raise LilyError(f"notes database error: {err}") from err

    def replace(self, source, chunks):
        """Store the chunks of one source, replacing what was there before."""
        try:
            with self.db:
                self.db.execute("DELETE FROM notes WHERE source = ?", (source,))
                self.db.executemany(
                    "INSERT INTO notes(source, body) VALUES (?, ?)", [(source, c) for c in chunks]
                )
        except sqlite3.Error as err:
            raise LilyError(f"notes database error: {err}") from err

    def search(self, match, limit):
        """Best matches first. `match` is an FTS5 expression. Returns (source, body) rows."""
        sql = "SELECT source, body FROM notes WHERE notes MATCH ? ORDER BY rank LIMIT ?"
        return self._query(sql, (match, limit))

    def sources(self):
        """Every source with its chunk count: [(source, count), ...]."""
        return self._query("SELECT source, count(*) FROM notes GROUP BY source ORDER BY source")

    def forget(self, source):
        """Remove one source. Returns how many chunks were removed."""
        count = sum(n for name, n in self.sources() if name == source)
        self._query("DELETE FROM notes WHERE source = ?", (source,))
        return count

    def close(self):
        self.db.close()
