import tempfile
import unittest
from pathlib import Path

from lily.llm.orchestrator import LLMOrchestrator
from lily.orchestrator import Lily
from lily.tools.base import BaseTool
from lily.tools.orchestrator import MAX_OUTPUT, ToolsOrchestrator
from lily.ui import commands
from lily.utils.errors import LilyError, ToolError
from tests.fakes import FakeProvider, make_settings, text_reply, tool_reply


class Shout(BaseTool):
    name = "shout"
    description = "Shout text\nsecond line"
    parameters = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    def run(self, text):
        return text.upper() * int(getattr(self, "times", 1))


class Crash(BaseTool):
    name = "crash"

    def run(self):
        raise RuntimeError("oops")


def setup(answer=True):
    lily = Lily(make_settings())
    lily.confirm = lambda question: answer
    empty = Path(tempfile.mkdtemp())
    tools = ToolsOrchestrator(lily, plugins_dir=empty, mcp_loader=lambda lily: ([], ["mcp x: down"]))
    tools.registry.register(Shout(lily))
    tools.registry.register(Crash(lily))
    lily.register(tools)
    return lily, tools


def call(name, **args):
    return {"id": "c1", "name": name, "args": args}


class ToolsOrchestratorTests(unittest.TestCase):
    def test_runs_a_tool(self):
        _, tools = setup()
        self.assertEqual(tools.run(None, call("shout", text="hi")), "HI")

    def test_unknown_tool_lists_the_available_ones(self):
        _, tools = setup()
        with self.assertRaisesRegex(ToolError, "no tool named 'nope'.*shout"):
            tools.run(None, call("nope"))

    def test_declined_tool_does_not_run(self):
        _, tools = setup(answer=False)
        with self.assertRaisesRegex(ToolError, "declined"):
            tools.run(None, call("shout", text="hi"))

    def test_a_crashing_tool_becomes_a_tool_error(self):
        _, tools = setup()
        with self.assertRaisesRegex(ToolError, "crash crashed: oops"):
            tools.run(None, call("crash"))

    def test_bad_arguments_are_refused_before_running(self):
        _, tools = setup()
        with self.assertRaisesRegex(ToolError, "missing"):
            tools.run(None, call("shout"))

    def test_long_output_is_cut_and_empty_output_is_labelled(self):
        _, tools = setup()
        tools.registry.get("shout").times = MAX_OUTPUT
        out = tools.run(None, call("shout", text="ab"))
        self.assertTrue(out.endswith(f"[output cut: {MAX_OUTPUT} more characters]"))
        self.assertEqual(len(out.split("\n")[0]), MAX_OUTPUT)
        self.assertEqual(tools.run(None, call("shout", text="  ")), "(no output)")
        tools.registry.get("shout").times = 0
        self.assertEqual(tools.run(None, call("shout", text="x")), "(no output)")

    def test_schemas_and_describe(self):
        _, tools = setup()
        self.assertIn("shout", [s["function"]["name"] for s in tools.schemas()])
        lines = tools.describe().splitlines()
        self.assertIn("shout: Shout text", lines)
        self.assertIn("problem: mcp x: down", lines)

    def test_reload_restores_the_default_tools(self):
        _, tools = setup()
        summary = tools.reload()
        self.assertEqual(tools.registry.get("shout"), None)
        self.assertIn("1 problem", summary)

    def test_slash_commands(self):
        lily, _ = setup()
        self.assertIn("shout: Shout text", commands.run(lily, "/tools"))
        self.assertIn("tools loaded", commands.run(lily, "/reload"))
        with self.assertRaises(LilyError):
            commands.run(Lily(make_settings()), "/tools")

    def test_full_turn_through_the_llm_and_the_tools_layer(self):
        lily, _ = setup()
        provider = FakeProvider(tool_reply("shout", {"text": "hey"}), text_reply("it said HEY"))
        lily.register(LLMOrchestrator(lily, provider))
        self.assertEqual(lily.handle("shout hey"), "it said HEY")
        self.assertIn("shout", [t["function"]["name"] for t in provider.payloads[0]["tools"]])
        self.assertEqual(provider.payloads[1]["messages"][-1]["content"], "HEY")

    def test_declined_tool_is_explained_to_the_model(self):
        lily, _ = setup(answer=False)
        provider = FakeProvider(tool_reply("shout", {"text": "hey"}), text_reply("ok, skipped"))
        lily.register(LLMOrchestrator(lily, provider))
        lily.handle("shout hey")
        self.assertIn("declined", provider.payloads[1]["messages"][-1]["content"])


if __name__ == "__main__":
    unittest.main()
