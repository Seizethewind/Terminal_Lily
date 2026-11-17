import unittest

from lily.bootstrap import build
from tests.fakes import make_settings


class BootstrapTests(unittest.TestCase):
    def test_every_layer_is_plugged_in(self):
        lily = build(make_settings())
        self.assertEqual(lily.router.names(), ["llm", "memory", "rag", "self", "tools"])


if __name__ == "__main__":
    unittest.main()
