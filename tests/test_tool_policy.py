"""Tests for the approval policy: what runs quietly, what asks, and the one-folder grant."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lily.state import State
from lily.tools import policy, shell_safety, tidy
from lily.tools.permissions import Permissions
from lily.tools.secrets import is_secret

QUIET = [
    "ls -la", "cat README.md", "git status", "grep -rn foo lily | head -5",
    'find . -name "*.py" | xargs grep -l "def remember" 2>/dev/null',
]
LOUD = [
    "rm -rf x", "echo hi > f", "cat a; rm b", 'python3 -c "print(1)"', "find . -delete",
    "find . -exec cat {} \\;", "git commit -m x", "ls && rm x", "cat $(whoami)", "cat .env", "ls | sh",
]


class ShellTests(unittest.TestCase):
    def test_looking_is_quiet(self):
        for command in QUIET:
            self.assertTrue(shell_safety.is_read_only(command), command)

    def test_changing_or_unknown_asks(self):
        for command in LOUD:
            self.assertFalse(shell_safety.is_read_only(command), command)

    def test_secrets(self):
        for secret in (".env", "~/.ssh/id_rsa", "api_token.txt"):
            self.assertTrue(is_secret(secret), secret)
        for fine in (".env.example", "notes.txt", "README.md"):
            self.assertFalse(is_secret(fine), fine)


class DecideTests(unittest.TestCase):
    def test_verdicts(self):
        cases = [
            ("read_file", {"path": "README.md"}, "allow"), ("read_file", {"path": ".env"}, "ask"),
            ("write_file", {"path": "a.txt"}, "write"), ("write_file", {"path": ".env"}, "ask"),
            ("shell", {"command": "ls"}, "allow"), ("shell", {"command": "rm x"}, "ask"),
            ("termux_api", {"action": "battery"}, "allow"), ("termux_api", {"action": "clipboard_set"}, "ask"),
            ("remember", {}, "allow"), ("approve_task", {}, "ask"), ("some_plugin", {}, "ask"),
        ]
        for name, args, verdict in cases:
            self.assertEqual(policy.decide(name, args), verdict, (name, args))


class GrantTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.asked, self.answer = [], True
        lily = SimpleNamespace(confirm=lambda question: self.asked.append(question) or self.answer)
        self.permissions = Permissions(lily)
        self.tool = SimpleNamespace(name="write_file")
        self.state = State("system", "fast", 20)
        self.state.add("user", "save my notes")

    def tearDown(self):
        self.dir.cleanup()

    def save(self, name, folder=None):
        args = {"path": str(Path(folder or self.dir.name) / name), "content": "hi"}
        return self.permissions.allow(self.tool, args, self.state)

    def test_one_question_per_folder_and_task(self):
        self.assertTrue(self.save("a.txt") and self.save("b.txt"))
        self.assertEqual(len(self.asked), 1)
        with tempfile.TemporaryDirectory() as other:
            self.assertTrue(self.save("c.txt", other))
        self.assertEqual(len(self.asked), 2)

    def test_next_message_asks_again(self):
        self.save("a.txt")
        self.state.add("assistant", "saved")
        self.state.add("user", "and another")
        self.save("b.txt")
        self.assertEqual(len(self.asked), 2)

    def test_no_means_no_grant(self):
        self.answer = False
        self.assertFalse(self.save("a.txt"))
        self.assertFalse(self.save("b.txt"))
        self.assertEqual(len(self.asked), 2)

    def test_question_is_short(self):
        self.assertEqual(tidy.short("a\nb\nc"), "a  (+2 more lines)")
        self.assertEqual(tidy.short(str(Path.home() / "x")), "~/x")


if __name__ == "__main__":
    unittest.main()
