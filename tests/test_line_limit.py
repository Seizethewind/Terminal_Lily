"""Enforces the house rule: no Python file longer than 120 lines."""
import unittest

from lily.utils.paths import ROOT

LIMIT = 120
SKIP = {".git", ".venv", "__pycache__", "data"}


class LineLimitTests(unittest.TestCase):
    def test_every_python_file_is_short_enough(self):
        too_long = []
        for path in ROOT.rglob("*.py"):
            if SKIP & set(path.relative_to(ROOT).parts):
                continue
            count = len(path.read_text(encoding="utf-8").splitlines())
            if count > LIMIT:
                too_long.append(f"{path.relative_to(ROOT)} ({count} lines)")
        self.assertEqual(too_long, [])


if __name__ == "__main__":
    unittest.main()
