"""Every turn with the user, kept forever in SQLite, plus lasting facts about them."""
import sqlite3
import time
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS turns (id INTEGER PRIMARY KEY, ts REAL, user TEXT, answer TEXT);
CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, ts REAL, text TEXT UNIQUE);
"""


class ChatMemory:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(SCHEMA)
        self.boundary = self._run("SELECT COALESCE(MAX(id), 0) FROM turns")[0][0]   # earlier sessions end here

    def _run(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(sql, args).fetchall()
            db.commit()
            return rows

    def save_turn(self, user, answer):
        self._run("INSERT INTO turns (ts, user, answer) VALUES (?, ?, ?)", (time.time(), user, answer))

    def earlier(self, count):
        """The last `count` turns of earlier sessions, oldest first."""
        sql = "SELECT user, answer FROM turns WHERE id <= ? ORDER BY id DESC LIMIT ?"
        return self._run(sql, (self.boundary, count))[::-1]

    def search(self, query, count=3):
        """Past turns that mention the longer words of `query` (newest first)."""
        words = [word for word in query.lower().split() if len(word) > 3][:4]
        if not words:
            return []
        clause = " OR ".join("LOWER(user || ' ' || answer) LIKE ?" for _ in words)
        sql = f"SELECT user, answer FROM turns WHERE {clause} ORDER BY id DESC LIMIT ?"
        return self._run(sql, [f"%{word}%" for word in words] + [count])

    def add_fact(self, text):
        if text.strip():
            self._run("INSERT OR IGNORE INTO facts (ts, text) VALUES (?, ?)", (time.time(), text.strip()))

    def facts(self, limit=40):
        rows = self._run("SELECT text FROM facts ORDER BY id DESC LIMIT ?", (limit,))
        return [row[0] for row in rows][::-1]
