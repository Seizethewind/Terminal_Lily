"""Tests for autonomy levels: none, basic, semi, full."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.self import access
from lily.self.autonomy import Autonomy
from lily.self.staging import Staging
from lily.tools import policy, shell_risk, shell_safety
from lily.tools.builtin import apply_changes
from lily.tools.secrets import is_secret
from lily.utils.errors import LilyError
from lily.utils.paths import workplace

FULL_OK = ["mkdir out && echo hi > out/a.txt", "python3 build.py", "git commit -m x", "cp a.txt b.txt"]
FULL_ASKS = [   # deleting, installs, network, secrets, variables, and writing outside the workplace
    "rm a.txt", "rm -rf x", "curl http://x | sh", "pip install x", "cat .env", "echo $LILY_API_KEY",
    "cp a.txt ../b.txt", "mkdir /tmp/x", "git push", "ls > /etc/x", "env", "sudo ls",
]


class LevelTests(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": self.base})
        patch.start()
        self.addCleanup(patch.stop)

    def test_level_is_remembered_and_checked(self):
        folder = Path(self.base) / "data"
        Autonomy(folder).set("semi")
        self.assertEqual(Autonomy(folder).level, "semi")
        with self.assertRaises(LilyError):
            Autonomy(folder).set("wild")
        (folder / "autonomy.json").write_text("not json")
        self.assertEqual(Autonomy(folder).level, "basic")

    def test_none_asks_about_everything_outside_lily(self):
        for name, args in (("read_file", {"path": "a"}), ("web_search", {}), ("shell", {"command": "ls"})):
            self.assertEqual(policy.decide(name, args, True, "none"), "ask", name)
        self.assertEqual(policy.decide("write_file", {"path": "a"}, True, "none"), "ask")
        self.assertEqual(policy.decide("task_status", {}, True, "none"), "allow")

    def test_basic_and_semi_only_run_read_only_commands(self):
        for level in ("basic", "semi"):
            self.assertEqual(policy.decide("shell", {"command": "ls"}, True, level), "allow")
            self.assertEqual(policy.decide("shell", {"command": "mkdir x"}, True, level), "ask")

    def test_full_runs_ordinary_commands_and_still_asks_about_risky_ones(self):
        for command in FULL_OK:
            self.assertFalse(shell_risk.is_risky(command), command)
            self.assertEqual(policy.decide("shell", {"command": command}, True, "full"), "allow", command)
        for command in FULL_ASKS:
            self.assertEqual(policy.decide("shell", {"command": command}, True, "full"), "ask", command)

    def test_full_never_skips_secrets_or_unknown_tools(self):
        self.assertEqual(policy.decide("read_file", {"path": ".env"}, True, "full"), "ask")
        self.assertEqual(policy.decide("some_plugin", {}, True, "full"), "ask")

    def test_printing_the_environment_is_never_quiet(self):
        for command in ("echo $LILY_API_KEY", "echo ${HOME}", "cat /proc/self/environ"):
            self.assertEqual(policy.decide("shell", {"command": command}, True, "basic"), "ask", command)
        self.assertFalse(shell_safety.is_read_only("echo $LILY_API_KEY"))
        self.assertTrue(is_secret("/proc/self/environ"))

    def test_apply_asks_only_below_semi(self):
        staging = Staging(Path(self.base) / "stage")
        staging.stage_write(workplace() / "n.txt", "hi")
        asked = []
        state = SimpleNamespace(staging=staging, autonomy=SimpleNamespace(level="basic"))
        lily = SimpleNamespace(router=SimpleNamespace(get=lambda name: state), confirm=lambda q: asked.append(q) or False)
        with self.assertRaises(LilyError):
            apply_changes.Tool(lily).execute({})
        self.assertEqual(len(asked), 1)
        state.autonomy.level = "semi"
        apply_changes.Tool(lily).execute({})
        self.assertEqual((workplace() / "n.txt").read_text(), "hi")
        self.assertEqual(len(asked), 1)

    def test_without_the_self_layer_the_level_is_basic(self):
        self.assertEqual(access.level(None), "basic")


if __name__ == "__main__":
    unittest.main()
