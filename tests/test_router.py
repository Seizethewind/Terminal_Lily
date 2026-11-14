import unittest

from lily.router import Router
from lily.utils.errors import LilyError


class Sub:
    def __init__(self, name):
        self.name = name


class RouterTests(unittest.TestCase):
    def test_register_and_get(self):
        router = Router()
        router.register(Sub("llm"))
        self.assertEqual(router.get("llm").name, "llm")
        self.assertIsNone(router.get("tools"))
        self.assertEqual(router.names(), ["llm"])

    def test_final_means_done(self):
        self.assertIsNone(Router().route({"type": "final"}))

    def test_tool_call_goes_to_tools(self):
        self.assertEqual(Router().route({"type": "tool_call"}), "tools")

    def test_unknown_type_is_an_error(self):
        with self.assertRaises(LilyError):
            Router().route({"type": "mystery"})


if __name__ == "__main__":
    unittest.main()
