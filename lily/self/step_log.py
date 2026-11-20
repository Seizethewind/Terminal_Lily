"""The steps of each task, kept in the same SQLite file as the task list."""
import sqlite3
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS steps (
    task_id INTEGER, n INTEGER, title TEXT, status TEXT DEFAULT 'pending',
    tries INTEGER DEFAULT 0, result TEXT DEFAULT '', PRIMARY KEY (task_id, n)
);
"""


class StepLog:
    def __init__(self, path):
        self.path = str(path)
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(SCHEMA)

    def _run(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(sql, args).fetchall()
            db.commit()
            return rows

    def add(self, task_id, titles):
        for n, title in enumerate(titles, 1):
            self._run("INSERT OR IGNORE INTO steps (task_id, n, title) VALUES (?, ?, ?)", (task_id, n, title))

    def rows(self, task_id):
        """(n, title, status, tries, result) for every step, in order."""
        sql = "SELECT n, title, status, tries, result FROM steps WHERE task_id=? ORDER BY n"
        return self._run(sql, (task_id,))

    def mark(self, task_id, n, status, result=None, add_try=False):
        sql = "UPDATE steps SET status=?, tries=tries+?, result=COALESCE(?, result) WHERE task_id=? AND n=?"
        self._run(sql, (status, 1 if add_try else 0, result, task_id, n))

    def reset(self, task_id):
        """Make failed and interrupted steps ready to run again."""
        self._run("UPDATE steps SET status='pending' WHERE task_id=? AND status != 'done'", (task_id,))

    def progress(self, task_id):
        """Where a multi-step task stands, or '' for a one-step task."""
        rows = self.rows(task_id)
        if len(rows) < 2:
            return ""
        left = [row for row in rows if row[2] != "done"]
        if not left:
            return f"all {len(rows)} steps done"
        n, title, _, tries, _ = left[0]
        return f"stopped at step {n} of {len(rows)}: {title} ({tries} tries); retry_task runs the rest"
