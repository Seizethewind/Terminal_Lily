import unittest

from lily.agent_loop import NO_LLM, AgentLoop
from lily.router import Router
from lily.state import State
from lily.utils.errors import ToolError

CALL = {"type": "tool_call", "id": "c1", "name": "t", "args": {}}
FINAL = {"type": "final", "text": "done"}


class FakeLLM:
    name = "llm"

    def __init__(self, results):
        self.results = list(results)

    def run(self, state):
        return self.results.pop(0) if self.results else CALL


class FakeTools:
    name = "tools"

    def __init__(self, fail=False):
        self.fail = fail

    def run(self, state, call):
        if self.fail:
            raise ToolError("boom")
        return "42"


class FakeRag:
    name = "rag"

    def run(self, state, query):
        state.context.append(f"note about {query}")


def make(*subs, max_steps=4):
    router = Router()
    for sub in subs:
        router.register(sub)
    return AgentLoop(router, max_steps), State()


class AgentLoopTests(unittest.TestCase):
    def test_no_llm_gives_clear_message(self):
        loop, state = make()
        self.assertEqual(loop.run(state, "hi"), NO_LLM)

    def test_plain_answer(self):
        loop, state = make(FakeLLM([FINAL]))
        self.assertEqual(loop.run(state, "hi"), "done")
        self.assertEqual([m["role"] for m in state.messages], ["user", "assistant"])

    def test_tool_round_trip(self):
        loop, state = make(FakeLLM([CALL, FINAL]), FakeTools())
        self.assertEqual(loop.run(state, "hi"), "done")
        roles = [m["role"] for m in state.messages]
        self.assertEqual(roles, ["user", "assistant", "tool", "assistant"])
        self.assertEqual(state.messages[2]["content"], "42")

    def test_tool_error_is_reported_to_the_model(self):
        loop, state = make(FakeLLM([CALL, FINAL]), FakeTools(fail=True))
        loop.run(state, "hi")
        self.assertEqual(state.messages[2]["content"], "Error: boom")

    def test_missing_tools_layer_is_reported(self):
        loop, state = make(FakeLLM([CALL, FINAL]))
        loop.run(state, "hi")
        self.assertIn("not installed", state.messages[2]["content"])

    def test_step_limit_stops_endless_tool_calls(self):
        loop, state = make(FakeLLM([]), FakeTools(), max_steps=3)
        self.assertIn("3 steps", loop.run(state, "hi"))

    def test_rag_context_is_filled_before_the_model_runs(self):
        loop, state = make(FakeLLM([FINAL]), FakeRag())
        loop.run(state, "cats")
        self.assertEqual(state.context, ["note about cats"])


if __name__ == "__main__":
    unittest.main()
