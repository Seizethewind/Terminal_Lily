"""Lessons (told by you) and summaries (written by Lily). Both are kept as notes."""
from lily.memory.db import now


def add(db, text, kind="lesson"):
    return db.write("INSERT INTO lessons(ts, kind, text) VALUES (?, ?, ?)", (now(), kind, text))


def all_lessons(db):
    """[(id, kind, text), ...] oldest first."""
    return db.rows("SELECT id, kind, text FROM lessons ORDER BY id")


def get(db, lesson_id):
    rows = db.rows("SELECT id, kind, text FROM lessons WHERE id = ?", (lesson_id,))
    return rows[0] if rows else None


def remove(db, lesson_id):
    db.write("DELETE FROM lessons WHERE id = ?", (lesson_id,))
