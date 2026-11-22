"""Tests for the audit fixes: nothing hidden in the allow question, wider secrets,
quiet reads stay inside the workplace, Lily's keys stay out of shell commands."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from config import settings
from lily.self.worker_tools import WorkerTools
from lily.tools import policy
from lily.tools.builtin.shell import Tool as Shell
from lily.tools.permissions import Permissions
from lily.tools.secrets import is_secret
from lily.utils import childenv

TAIL = "echo the-hidden-tail"


class PromptTests(unittest.TestCase):
    def test_the_question_shows_the_whole_command(self):
        asked = []
        lily = SimpleNamespace(confirm=lambda question: asked.append(question) or True)
        command = f"echo {'a' * 300} && {TAIL}\nsecond line"
        Permissions(lily).allow(SimpleNamespace(name="shell"), {"command": command})
        self.assertIn(TAIL, asked[0])
        self.assertIn("second line", asked[0])

    def test_a_worker_approval_shows_the_whole_command(self):
        seen = []
        hive = SimpleNamespace(request=lambda task, text, wait: seen.append(text) or True)
        worker = WorkerTools.__new__(WorkerTools)
        worker.hive, worker.task_id, worker.wait, worker.grants = hive, 1, 5, set()
        worker._approved(SimpleNamespace(name="shell"), {"command": f"echo {'a' * 300} && {TAIL}"}, "ask")
        self.assertIn(TAIL, seen[0])


class SecretTests(unittest.TestCase):
    def test_history_and_token_files_count_as_secrets(self):
        for path in ("~/.bash_history", ".zsh_history", "~/.config/gh/hosts.yml", "repo/.git/config",
                     "~/.docker/config.json", "~/.kube/config", "~/.npmrc"):
            self.assertTrue(is_secret(path), path)
        for fine in ("~/.config/ghostty/config", "notes.txt", "src/config.py"):
            self.assertFalse(is_secret(fine), fine)


class QuietStaysInsideTests(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.dict(os.environ, {"LILY_WORKPLACE_DIR": tempfile.mkdtemp()})
        patch.start()
        self.addCleanup(patch.stop)

    def test_reading_a_file_outside_the_workplace_asks(self):
        for path in ("/etc/hosts", "~/notes.txt", "../x"):
            self.assertEqual(policy.decide("read_file", {"path": path}), "ask", path)
        self.assertEqual(policy.decide("read_file", {"path": "notes.txt"}), "allow")

    def test_read_only_commands_that_reach_outside_ask_at_every_level(self):
        for command in ("cat /etc/hosts", "grep -r token ~", "ls ..", "find / -name x"):
            for level in ("basic", "semi", "full"):
                self.assertEqual(policy.decide("shell", {"command": command}, True, level), "ask", command)
        for command in ("ls -la", "cat notes.txt", "grep -rn foo src | head -5", "find . -name '*.py'"):
            self.assertEqual(policy.decide("shell", {"command": command}), "allow", command)

    def test_a_long_search_query_asks(self):
        self.assertEqual(policy.decide("web_search", {"query": "rust lifetimes"}), "allow")
        self.assertEqual(policy.decide("web_search", {"query": "x" * (policy.QUERY_MAX + 1)}), "ask")


class ChildEnvTests(unittest.TestCase):
    def test_shell_commands_do_not_inherit_lilys_key(self):
        with mock.patch.dict(os.environ, {"LILY_API_KEY": "dummy-key-for-test"}):
            out = Shell(None).execute({"command": "echo key=${LILY_API_KEY:-gone}"})
        self.assertIn("key=gone", out)

    def test_every_name_in_dot_env_is_hidden_from_commands(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ), \
                mock.patch.object(childenv, "HIDDEN", set(childenv.HIDDEN)):
            path = Path(folder) / ".env"
            path.write_text("MCP_TOKEN=abc\n# a note\nLILY_TIMEOUT=5\n", encoding="utf-8")
            settings.load_env(path)
            env = childenv.clean()
        self.assertNotIn("MCP_TOKEN", env)
        self.assertNotIn("LILY_TIMEOUT", env)
        self.assertIn("PATH", env)


if __name__ == "__main__":
    unittest.main()
