import unittest

from lily.tools.base import BaseTool, to_int
from lily.tools.permissions import Permissions
from lily.tools.registry import Registry
from lily.utils.errors import ToolError


class Echo(BaseTool):
    name = "echo"
    description = "Echo text"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    def run(self, text):
        return text.upper()


class Lily:
    def __init__(self, answer):
        self.answer, self.asked = answer, []

    def confirm(self, question):
        self.asked.append(question)
        return self.answer


class BaseToolTests(unittest.TestCase):
    def test_schema_is_openai_style(self):
        schema = Echo(None).schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "echo")
        self.assertEqual(schema["function"]["parameters"]["required"], ["text"])

    def test_execute_runs_and_returns_text(self):
        self.assertEqual(Echo(None).execute({"text": "hi"}), "HI")

    def test_missing_and_unknown_arguments_are_refused(self):
        with self.assertRaisesRegex(ToolError, "missing"):
            Echo(None).execute({})
        with self.assertRaisesRegex(ToolError, "unknown"):
            Echo(None).execute({"text": "x", "extra": 1})

    def test_to_int(self):
        self.assertEqual(to_int("5", "n"), 5)
        self.assertEqual(to_int(None, "n", 7), 7)
        with self.assertRaises(ToolError):
            to_int("many", "n")


class RegistryTests(unittest.TestCase):
    def test_register_get_names_schemas(self):
        registry = Registry()
        registry.register(Echo(None))
        self.assertIs(registry.get("echo").name, "echo")
        self.assertEqual(registry.names(), ["echo"])
        self.assertEqual(registry.schemas()[0]["function"]["name"], "echo")
        registry.clear()
        self.assertEqual(registry.names(), [])

    def test_duplicate_and_invalid_names_are_refused(self):
        registry = Registry()
        registry.register(Echo(None))
        with self.assertRaisesRegex(ToolError, "duplicate"):
            registry.register(Echo(None))
        bad = Echo(None)
        bad.name = "has space"
        with self.assertRaisesRegex(ToolError, "invalid"):
            registry.register(bad)


class PermissionsTests(unittest.TestCase):
    def test_asks_with_tool_name_and_arguments(self):
        lily = Lily(True)
        self.assertTrue(Permissions(lily).allow(Echo(None), {"text": "rm -rf"}))
        self.assertIn("echo", lily.asked[0])
        self.assertIn("rm -rf", lily.asked[0])

    def test_no_means_no(self):
        self.assertFalse(Permissions(Lily(False)).allow(Echo(None), {}))

    def test_very_long_arguments_are_shortened(self):
        lily = Lily(True)
        Permissions(lily).allow(Echo(None), {"text": "x" * 5000})
        self.assertLess(len(lily.asked[0]), 1200)


if __name__ == "__main__":
    unittest.main()
