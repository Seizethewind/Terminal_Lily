"""Shared test doubles for the LLM and tools layer tests."""
import json

from config.settings import Settings
from lily.llm.base import Reply

PROFILES = {"auto": "auto", "fast": "auto:fast", "smart": "auto:smart"}
SCHEMA = {"type": "function", "function": {"name": "shell"}}


def make_settings(rules=None):
    return Settings(
        base_url="http://x/v1", api_key="", profiles=PROFILES, profile="auto",
        system_prompt="sys", rules=rules if rules is not None else {"smart": ["code"]},
    )


def text_reply(text):
    return Reply({"choices": [{"message": {"content": text}}]}, "prov/model")


def tool_reply(name="shell", args=None):
    fn = {"name": name, "arguments": json.dumps({"cmd": "ls"} if args is None else args)}
    call = {"id": "c1", "type": "function", "function": fn}
    return Reply({"choices": [{"message": {"tool_calls": [call]}}]}, "prov/model")


class FakeProvider:
    def __init__(self, *replies):
        self.replies, self.payloads = list(replies), []

    def chat(self, payload):
        self.payloads.append(payload)
        return self.replies.pop(0)


class FakeTools:
    name = "tools"

    def __init__(self):
        self.calls = []

    def schemas(self):
        return [SCHEMA]

    def run(self, state, call):
        self.calls.append(call)
        return "file.txt"
