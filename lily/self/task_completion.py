"""The list of tasks the workers started, finished or failed, kept in SQLite."""
import sqlite3
import time
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, task TEXT, status TEXT,
    done_by TEXT DEFAULT '', result TEXT DEFAULT '', started REAL, ended REAL, seen INTEGER DEFAULT 0
);
"""
COLUMNS = "id, role, task, status, done_by, result"


class TaskLog:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(SCHEMA)
        # A task still 'running' belongs to a Lily that was closed: it can never finish now.
        self._run("UPDATE tasks SET status='failed', result='interrupted when Lily closed' WHERE status='running'")

    def _run(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as db:
            cur = db.execute(sql, args)
            rows = cur.fetchall()
            db.commit()
            return cur.lastrowid, rows

    def start(self, role, task):
        sql = "INSERT INTO tasks (role, task, status, started) VALUES (?, ?, 'running', ?)"
        return self._run(sql, (role, task, time.time()))[0]

    def finish(self, task_id, status, result, done_by):
        sql = "UPDATE tasks SET status=?, result=?, done_by=?, ended=? WHERE id=?"
        self._run(sql, (status, result, done_by, time.time(), task_id))

    def completed(self, count=10):
        """Finished and failed tasks, newest first."""
        sql = f"SELECT {COLUMNS} FROM tasks WHERE status != 'running' ORDER BY id DESC LIMIT ?"
        return self._run(sql, (count,))[1]

    def unseen(self):
        """Finished tasks Lily has not told the user about yet."""
        sql = f"SELECT {COLUMNS} FROM tasks WHERE status != 'running' AND seen = 0 ORDER BY id"
        return self._run(sql)[1]

    def mark_seen(self, ids):
        for task_id in ids:
            self._run("UPDATE tasks SET seen=1 WHERE id=?", (task_id,))

    @staticmethod
    def line(row):
        task_id, role, task, status, done_by, result = row
        return f"#{task_id} {role} ({status}, by {done_by or 'nobody'}): {task[:60]} -> {result[:300]}"
