import unittest

from lily.tools import policy


class FullWritesTests(unittest.TestCase):
    def test_full_writes_inside_the_workplace_without_asking(self):
        for name in ("write_file", "edit_file"):
            self.assertEqual(policy.decide(name, {"path": "a.txt"}, level="full"), "allow")

    def test_full_still_asks_for_secrets_and_outside_paths(self):
        for path in (".env", "~/.ssh/id_rsa", "/etc/hosts", "../elsewhere.txt"):
            self.assertEqual(policy.decide("write_file", {"path": path}, level="full"), "ask", path)

    def test_lower_levels_are_unchanged(self):
        for level in ("basic", "semi"):
            self.assertEqual(policy.decide("write_file", {"path": "a.txt"}, level=level), "write")
        self.assertEqual(policy.decide("write_file", {"path": "a.txt"}, level="none"), "ask")

    def test_full_still_asks_about_other_things(self):
        self.assertEqual(policy.decide("shell", {"command": "rm x"}, level="full"), "ask")
        self.assertEqual(policy.decide("some_plugin", {}, level="full"), "ask")


if __name__ == "__main__":
    unittest.main()
