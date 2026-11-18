import unittest

from lily.bootstrap import build
from lily.llm.orchestrator import LLMOrchestrator
from lily.orchestrator import Lily
from lily.self.config import SelfConfig
from lily.self.router import ModelRouter
from lily.state import State
from lily.utils.errors import LLMError
from tests.fakes import (SCHEMA, FakeProvider, FakeTools, make_settings,
                         text_reply, tool_reply)


def setup(*replies, rules=None, profile="auto"):
    lily = Lily(make_settings(rules))
    lily.state.profile = profile
    provider = FakeProvider(*replies)
    llm = LLMOrchestrator(lily, provider)
    lily.register(llm)
    return lily, llm, provider


class OrchestratorTests(unittest.TestCase):
    def test_default_profile_sends_auto_with_system_prompt_first(self):
        lily, llm, provider = setup(text_reply("hello"))
        self.assertEqual(lily.handle("hi"), "hello")
        payload = provider.payloads[0]
        self.assertEqual(payload["model"], "auto")
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "sys"})
        self.assertNotIn("tools", payload)

    def test_remembers_which_model_really_answered(self):
        lily, llm, _ = setup(text_reply("hello"))
        lily.handle("hi")
        self.assertEqual(llm.last_routed_via, "prov/model")

    def test_trigger_word_switches_to_smart(self):
        lily, _, provider = setup(text_reply("ok"))
        lily.handle("help me with my code")
        self.assertEqual(provider.payloads[0]["model"], "auto:smart")

    def test_profile_set_by_hand_beats_trigger_words(self):
        lily, _, provider = setup(text_reply("ok"), profile="fast")
        lily.handle("help me with my code")
        self.assertEqual(provider.payloads[0]["model"], "auto:fast")

    def test_rule_pointing_at_unknown_profile_falls_back(self):
        lily, _, provider = setup(text_reply("ok"), rules={"turbo": ["code"]})
        lily.handle("my code")
        self.assertEqual(provider.payloads[0]["model"], "auto")

    def test_tool_schemas_are_offered_when_a_tools_layer_exists(self):
        lily, _, provider = setup(text_reply("ok"))
        lily.register(FakeTools())
        lily.handle("hi")
        self.assertEqual(provider.payloads[0]["tools"], [SCHEMA])

    def test_full_turn_with_a_tool_call(self):
        lily, _, provider = setup(tool_reply(), text_reply("I see file.txt"))
        tools = FakeTools()
        lily.register(tools)
        self.assertEqual(lily.handle("list files"), "I see file.txt")
        self.assertEqual(tools.calls[0]["args"], {"cmd": "ls"})
        second = provider.payloads[1]["messages"]
        self.assertEqual([m["role"] for m in second[-2:]], ["assistant", "tool"])
        self.assertEqual(second[-1]["content"], "file.txt")

    def test_bootstrap_finds_the_llm_layer(self):
        lily = build(make_settings())
        self.assertIsInstance(lily.router.get("llm"), LLMOrchestrator)

    def test_state_view_is_what_gets_sent(self):
        state = State("sys")
        state.add("user", "hi")
        _, llm, provider = setup(text_reply("yo"))
        llm.run(state)
        self.assertEqual(provider.payloads[0]["messages"], state.view())


class _Down:
    def chat(self, payload):
        raise LLMError("down")


class _SelfLayer:
    name = "self"

    def __init__(self, models):
        self.models = models

    def run(self, state, **kwargs):
        return ""


class FallbackTests(unittest.TestCase):
    def chat_with(self, lily_provider, workers_provider):
        models = ModelRouter(SelfConfig({}), {"lily": lily_provider, "workers": workers_provider},
                             clock=lambda: 0.0)
        lily = Lily(make_settings())
        lily.register(_SelfLayer(models))
        lily.register(LLMOrchestrator(lily))
        return lily.handle("hi")

    def test_chat_uses_lily_router_first(self):
        workers = FakeProvider()
        self.assertEqual(self.chat_with(FakeProvider(text_reply("from lily")), workers), "from lily")
        self.assertEqual(workers.payloads, [])

    def test_chat_falls_back_to_workers_router(self):
        workers = FakeProvider(text_reply("from workers"))
        self.assertEqual(self.chat_with(_Down(), workers), "from workers")
        self.assertEqual(workers.payloads[0]["model"], "auto")


if __name__ == "__main__":
    unittest.main()
