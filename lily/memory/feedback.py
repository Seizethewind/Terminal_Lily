"""Your verdict on an answer (/good or /bad). One rating per run; the last one counts."""
from lily.memory.db import now


def rate(db, run_id, rating, note=""):
    db.write("DELETE FROM feedback WHERE run_id = ?", (run_id,))
    db.write(
        "INSERT INTO feedback(run_id, rating, note, ts) VALUES (?, ?, ?, ?)",
        (run_id, 1 if rating > 0 else -1, note, now()),
    )


def rating_of(db, run_id):
    rows = db.rows("SELECT rating FROM feedback WHERE run_id = ?", (run_id,))
    return rows[0][0] if rows else None
