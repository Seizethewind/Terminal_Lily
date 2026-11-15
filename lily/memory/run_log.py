"""The run log: one row for every message Lily answers."""
import json

from lily.memory.db import now

COLUMNS = ("id", "ts", "profile", "routed_via", "user_text", "answer", "tools", "steps", "latency_ms", "error")


def record(db, rec):
    """Store one finished turn and return its id."""
    sql = ("INSERT INTO runs(ts, profile, routed_via, user_text, answer, tools, steps, latency_ms, error) "
           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
    return db.write(sql, (
        now(), rec.get("profile", ""), rec.get("routed_via", ""), rec.get("user_text", ""),
        rec.get("answer", ""), json.dumps(rec.get("tools", [])), rec.get("steps", 0),
        rec.get("latency_ms", 0), rec.get("error", ""),
    ))


def recent(db, limit=10):
    """The newest runs first, as dicts."""
    rows = db.rows(f"SELECT {', '.join(COLUMNS)} FROM runs ORDER BY id DESC LIMIT ?", (limit,))
    runs = [dict(zip(COLUMNS, row)) for row in rows]
    for run in runs:
        run["tools"] = json.loads(run["tools"] or "[]")
    return runs


def stats(db):
    """Per profile: [(profile, runs, good, bad), ...]."""
    sql = ("SELECT r.profile, count(DISTINCT r.id), coalesce(sum(f.rating > 0), 0), "
           "coalesce(sum(f.rating < 0), 0) FROM runs r LEFT JOIN feedback f ON f.run_id = r.id "
           "GROUP BY r.profile ORDER BY r.profile")
    return db.rows(sql)
