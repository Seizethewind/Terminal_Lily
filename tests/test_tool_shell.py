import unittest

from lily.tools.builtin.shell import Tool
from lily.utils.errors import ToolError


class ShellTests(unittest.TestCase):
    def setUp(self):
        self.tool = Tool(None)

    def test_returns_exit_code_and_output(self):
        self.assertEqual(self.tool.execute({"command": "echo hello"}), "exit code 0\nhello")

    def test_failing_command_reports_its_exit_code(self):
        self.assertTrue(self.tool.execute({"command": "exit 3"}).startswith("exit code 3"))

    def test_error_output_is_included(self):
        out = self.tool.execute({"command": "echo oops 1>&2"})
        self.assertIn("oops", out)

    def test_long_running_command_is_stopped(self):
        with self.assertRaisesRegex(ToolError, "stopped after 1 seconds"):
            self.tool.execute({"command": "sleep 5", "timeout": 1})

    def test_timeout_is_limited_and_validated(self):
        with self.assertRaises(ToolError):
            self.tool.execute({"command": "true", "timeout": "soon"})
        self.assertIn("exit code 0", self.tool.execute({"command": "true", "timeout": "5"}))

    def test_commands_cannot_wait_for_keyboard_input(self):
        out = self.tool.execute({"command": "cat", "timeout": 5})
        self.assertEqual(out, "exit code 0\n")


if __name__ == "__main__":
    unittest.main()
