"""Tests for named model roles: tiers per job, /roles changes that stick, task titles."""
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.llm.base import Reply
from lily.self import namer
from lily.self.config import SelfConfig
from lily.self.dispatcher import Dispatcher
from lily.self.hive_mind import HiveMind
from lily.self.roles import Roles
from lily.self.router import ModelRouter
from lily.self.step_log import StepLog
from lily.self.sub_agent import SubAgent
from lily.self.task_completion import TaskLog
from lily.utils.errors import LilyError

LONG = "write a small script that renames every photo by date"


def reply(text):
    return Reply({"choices": [{"message": {"content": text}}]}, "fake")


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.folder = Path(self.dir.name)

    def test_every_job_has_a_tier_and_unknown_roles_use_the_default(self):
        models = ModelRouter(SelfConfig({}), providers={})
        self.assertEqual([models.role_tier(r) for r in ("planner", "namer", "coder", "takeover")], ["light", "light", "heavy", "heavy"])
        self.assertEqual(models.role_tier("gardener"), "normal")
        self.assertEqual(ModelRouter(SelfConfig({"roles": {"coder": "huge"}}), providers={}).role_tier("coder"), "normal")

    def test_a_change_is_validated_remembered_and_beats_the_config(self):
        cfg = SelfConfig({"roles": {"coder": "light"}})
        roles = Roles(cfg, self.folder)
        roles.set("Coder", "heavy")
        roles.set("gardener", "light")
        for role, tier in (("coder", "fast"), ("bad name!", "light")):
            with self.assertRaises(LilyError):
                roles.set(role, tier)
        again = SelfConfig({"roles": {"coder": "light"}})
        Roles(again, self.folder)
        self.assertEqual((again.roles["coder"], again.roles["gardener"]), ("heavy", "light"))

    def test_the_table_lists_jobs_custom_roles_and_the_default(self):
        cfg = SelfConfig({"roles": {"gardener": "light"}})
        text = Roles(cfg, self.folder).describe(ModelRouter(cfg, providers={}))
        for wanted in ("planner", "namer", "takeover", "gardener", "your own role", "default", "auto:smart"):
            self.assertIn(wanted, text)

    def test_a_takeover_uses_the_takeover_role_tier(self):
        limits = {"approval_wait": 1, "worker_steps": 2}
        models = SimpleNamespace(tier=lambda *a: "normal", role_tier=lambda role: {"takeover": "light"}[role])
        kit = SimpleNamespace(models=models, hive=HiveMind(), cfg=SimpleNamespace(limits=limits))
        self.assertEqual(SubAgent(SimpleNamespace(), kit, 1, "coder", "t", kind="lily").tier, "light")
        self.assertEqual(SubAgent(SimpleNamespace(), kit, 1, "coder", "t").tier, "normal")


class TitleTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def test_the_title_is_cleaned_and_kept_short(self):
        fake = SimpleNamespace(tier=lambda *a: "light", chat=lambda *a: reply('"Rename photos by date."\nextra words'))
        self.assertEqual(namer.make_title(fake, LONG), "Rename photos by date")

    def test_an_old_task_file_gets_the_title_column_and_keeps_its_rows(self):
        path = Path(self.dir.name) / "old.db"
        with sqlite3.connect(path) as db:
            db.executescript("CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, task TEXT, "
                             "status TEXT, done_by TEXT DEFAULT '', result TEXT DEFAULT '', started REAL, ended REAL, "
                             "seen INTEGER DEFAULT 0); INSERT INTO tasks (role, task, status) VALUES ('coder', 'old job', 'done');")
        log = TaskLog(path)
        self.assertEqual(log.get(1)[2], "old job")
        log.rename(1, "Old title")
        self.assertIn("Old title", log.line(log.get(1)))
        self.assertIn("old job", log.line(log.get(1)[:6]))

    def test_a_long_task_gets_a_title_in_the_background(self):
        def chat(kind, tier, messages, tools=None):
            return reply("Photo renamer script" if messages[0]["content"].startswith("Give the task") else "1. only one")
        path = Path(self.dir.name) / "t.db"
        models = SimpleNamespace(busy=0, tier=lambda *a: "light", role_tier=lambda r: "light", chat=chat)
        limits = {"max_workers": 3, "step_tries": 1, "max_plan_steps": 4, "plan_min_chars": 0}
        kit = SimpleNamespace(cfg=SimpleNamespace(limits=limits), hive=HiveMind(), steps=StepLog(path), models=models)
        tasks = TaskLog(path)
        agent = SimpleNamespace(run=lambda: "done")
        with mock.patch("lily.self.step_runner.SubAgent", lambda *a, **k: agent):
            Dispatcher(None, kit, tasks).submit("coder", LONG)
            end = time.time() + 5
            while time.time() < end and not (tasks.completed() and tasks.completed()[0][6]):
                time.sleep(0.02)
        self.assertEqual(tasks.completed()[0][6], "Photo renamer script")


if __name__ == "__main__":
    unittest.main()
