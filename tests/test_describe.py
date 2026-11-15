import unittest

from lily.tools.describe import LIMIT, describe
from lily.tools.permissions import Permissions


class Tool:
    def __init__(self, name):
        self.name = name


class Lily:
    def __init__(self):
        self.asked = []
        self.confirm = lambda question: self.asked.append(question) or True


class DescribeTests(unittest.TestCase):
    def test_shell_says_what_it_is_and_shows_the_command(self):
        self.assertEqual(describe("shell", {"command": "ls -la"}), ("run a command on your phone", ["ls -la"]))

    def test_files_and_searches(self):
        self.assertEqual(describe("read_file", {"path": "~/a.txt"}), ("read a file", ["~/a.txt"]))
        self.assertEqual(describe("web_search", {"query": "rust"}), ("search the web", ["rust"]))
        self.assertEqual(describe("rag_search", {"query": "x"})[0], "look through her saved notes")

    def test_write_file_shows_the_path_and_size_not_the_content(self):
        what, details = describe("write_file", {"path": "a.txt", "content": "hello"})
        self.assertEqual((what, details), ("write to a file", ["a.txt", "(5 characters of text)"]))
        self.assertEqual(describe("write_file", {"path": "a", "content": "", "append": True})[0],
                         "add text to the end of a file")

    def test_termux_actions_read_like_english(self):
        self.assertEqual(describe("termux_api", {"action": "battery"}), ("check your battery", []))
        what, details = describe("termux_api", {"action": "notify", "title": "Hi", "text": "yo"})
        self.assertEqual((what, details), ("show a notification", ["Hi", "yo"]))
        self.assertEqual(describe("termux_api", {"action": "weird"})[0], "use your phone")

    def test_unknown_tools_still_get_a_readable_question(self):
        what, details = describe("lilyai__find", {"query": "cats", "limit": 3})
        self.assertEqual(what, "use the tool 'lilyai__find'")
        self.assertEqual(details, ["query: cats", "limit: 3"])

    def test_missing_arguments_do_not_crash_and_long_ones_are_cut(self):
        self.assertEqual(describe("shell", {}), ("run a command on your phone", []))
        _, (line,) = describe("shell", {"command": "x" * (LIMIT + 50)})
        self.assertTrue(line.endswith("(50 more characters)"))

    def test_the_question_has_no_json_in_it(self):
        lily = Lily()
        Permissions(lily).allow(Tool("shell"), {"command": 'echo "hi" && ls', "timeout": 90})
        question = lily.asked[0]
        self.assertEqual(question.splitlines()[0], "Lily wants to run a command on your phone:")
        self.assertIn('    echo "hi" && ls', question)
        self.assertNotIn("{", question)
        self.assertNotIn("timeout", question)


if __name__ == "__main__":
    unittest.main()
