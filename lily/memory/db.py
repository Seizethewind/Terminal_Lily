"""The one SQLite file behind the data layer (data/lily.db). Only this file opens it."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from lily.utils.errors import LilyError

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY, ts TEXT, profile TEXT, routed_via TEXT, user_text TEXT,
    answer TEXT, tools TEXT, steps INTEGER, latency_ms INTEGER, error TEXT);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY, run_id INTEGER, rating INTEGER, note TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY, ts TEXT, kind TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS code_blocks (
    id INTEGER PRIMARY KEY, run_id INTEGER, source TEXT, language TEXT, grp TEXT, family TEXT,
    known INTEGER, guessed INTEGER, lines INTEGER, code TEXT);
CREATE INDEX IF NOT EXISTS code_blocks_language ON code_blocks(language);
CREATE TABLE IF NOT EXISTS entity_terms (name TEXT PRIMARY KEY, cls TEXT, sub TEXT);
CREATE TABLE IF NOT EXISTS entity_mentions (
    id INTEGER PRIMARY KEY, run_id INTEGER, name TEXT, cls TEXT, sub TEXT, count INTEGER);
CREATE INDEX IF NOT EXISTS entity_mentions_name ON entity_mentions(name);
CREATE TABLE IF NOT EXISTS taxonomy_nodes (path TEXT PRIMARY KEY, description TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS taxonomy_labels (
    id INTEGER PRIMARY KEY, kind TEXT, ref TEXT, path TEXT, source TEXT, ts TEXT,
    UNIQUE (kind, ref, path));
CREATE INDEX IF NOT EXISTS taxonomy_labels_path ON taxonomy_labels(path);
CREATE TABLE IF NOT EXISTS dictionary (
    term TEXT PRIMARY KEY, label TEXT, meaning TEXT, path TEXT, aliases TEXT, ts TEXT);
"""

# Full-text index over the chats, kept in step by triggers. Separate so a SQLite without FTS5 still works.
FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS runs_fts USING fts5(
    user_text, answer, content='runs', content_rowid='id', tokenize='porter unicode61');
CREATE TRIGGER IF NOT EXISTS runs_fts_insert AFTER INSERT ON runs BEGIN
    INSERT INTO runs_fts(rowid, user_text, answer) VALUES (new.id, new.user_text, new.answer);
END;
CREATE TRIGGER IF NOT EXISTS runs_fts_delete AFTER DELETE ON runs BEGIN
    INSERT INTO runs_fts(runs_fts, rowid, user_text, answer) VALUES ('delete', old.id, old.user_text, old.answer);
END;
CREATE TRIGGER IF NOT EXISTS runs_fts_update AFTER UPDATE ON runs BEGIN
    INSERT INTO runs_fts(runs_fts, rowid, user_text, answer) VALUES ('delete', old.id, old.user_text, old.answer);
    INSERT INTO runs_fts(rowid, user_text, answer) VALUES (new.id, new.user_text, new.answer);
END;
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _guard():
    try:
        yield
    except (sqlite3.Error, OSError) as err:
        raise LilyError(f"data layer error: {err}") from err


class Database:
    def __init__(self, path):
        with _guard():
            if str(path) != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(path))
            self.db.executescript(SCHEMA)
            self.fts = self._start_index()

    def _start_index(self):
        """Create the chat index and add chats saved before it existed. False if SQLite has no FTS5."""
        try:
            self.db.executescript(FTS_SCHEMA)
            saved = self.db.execute("SELECT count(*) FROM runs").fetchone()[0]
            if saved != self.db.execute("SELECT count(*) FROM runs_fts_docsize").fetchone()[0]:
                with self.db:
                    self.db.execute("INSERT INTO runs_fts(runs_fts) VALUES ('rebuild')")
            return True
        except sqlite3.OperationalError:
            return False

    def write(self, sql, params=()):
        """Run a change and return the new row id."""
        with _guard(), self.db:
            return self.db.execute(sql, params).lastrowid

    def rows(self, sql, params=()):
        with _guard():
            return self.db.execute(sql, params).fetchall()
