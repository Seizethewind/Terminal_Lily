import tempfile
import unittest
from pathlib import Path

from lily.memory import feedback, lessons, run_log
from lily.memory.db import Database
from lily.utils.errors import LilyError


def rec(text="hi", answer="hello", profile="fast", **extra):
    return {"user_text": text, "answer": answer, "profile": profile, **extra}


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def test_runs_are_recorded_newest_first_with_tools(self):
        run_log.record(self.db, rec("one", tools=["shell"], steps=2, latency_ms=40, routed_via="p/m"))
        run_log.record(self.db, rec("two", error="boom", answer=""))
        runs = run_log.recent(self.db, 5)
        self.assertEqual([r["user_text"] for r in runs], ["two", "one"])
        self.assertEqual(runs[1]["tools"], ["shell"])
        self.assertEqual((runs[1]["steps"], runs[1]["routed_via"]), (2, "p/m"))
        self.assertEqual(runs[0]["error"], "boom")

    def test_recent_respects_the_limit(self):
        for n in range(5):
            run_log.record(self.db, rec(str(n)))
        self.assertEqual(len(run_log.recent(self.db, 2)), 2)

    def test_last_rating_wins(self):
        run_id = run_log.record(self.db, rec())
        self.assertIsNone(feedback.rating_of(self.db, run_id))
        feedback.rate(self.db, run_id, 1)
        feedback.rate(self.db, run_id, -1, "wrong")
        self.assertEqual(feedback.rating_of(self.db, run_id), -1)
        self.assertEqual(len(self.db.rows("SELECT * FROM feedback")), 1)

    def test_stats_per_profile(self):
        good = run_log.record(self.db, rec(profile="fast"))
        bad = run_log.record(self.db, rec(profile="fast"))
        run_log.record(self.db, rec(profile="smart"))
        feedback.rate(self.db, good, 1)
        feedback.rate(self.db, bad, -1)
        self.assertEqual(run_log.stats(self.db), [("fast", 2, 1, 1), ("smart", 1, 0, 0)])

    def test_lessons_add_get_remove(self):
        number = lessons.add(self.db, "short answers")
        lessons.add(self.db, "a recap", kind="summary")
        self.assertEqual(lessons.get(self.db, number), (number, "lesson", "short answers"))
        self.assertEqual([k for _, k, _ in lessons.all_lessons(self.db)], ["lesson", "summary"])
        lessons.remove(self.db, number)
        self.assertIsNone(lessons.get(self.db, number))

    def test_database_file_is_created_with_its_folder(self):
        path = Path(tempfile.mkdtemp()) / "deeper" / "lily.db"
        Database(path)
        self.assertTrue(path.exists())

    def test_unusable_path_is_a_lily_error(self):
        blocker = Path(tempfile.mkdtemp()) / "file"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(LilyError, "data layer error"):
            Database(blocker / "lily.db")


if __name__ == "__main__":
    unittest.main()
