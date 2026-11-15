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

    def write(self, sql, params=()):
        """Run a change and return the new row id."""
        with _guard(), self.db:
            return self.db.execute(sql, params).lastrowid

    def rows(self, sql, params=()):
        with _guard():
            return self.db.execute(sql, params).fetchall()
