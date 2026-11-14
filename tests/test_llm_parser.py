import unittest

from lily.llm.parser import parse
from lily.utils.errors import LLMError


def reply(message):
    return {"choices": [{"message": message}]}


def call(name="shell", args='{"cmd": "ls"}', call_id="c1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


class ParserTests(unittest.TestCase):
    def test_plain_answer_is_final_and_stripped(self):
        step = parse(reply({"content": "  hello \n"}))
        self.assertEqual(step, {"type": "final", "text": "hello"})

    def test_tool_call_with_json_string_arguments(self):
        step = parse(reply({"content": None, "tool_calls": [call()]}))
        self.assertEqual(step["type"], "tool_call")
        self.assertEqual((step["id"], step["name"], step["args"]), ("c1", "shell", {"cmd": "ls"}))

    def test_tool_call_with_dict_arguments(self):
        step = parse(reply({"tool_calls": [call(args={"a": 1})]}))
        self.assertEqual(step["args"], {"a": 1})

    def test_missing_id_and_empty_arguments_get_defaults(self):
        step = parse(reply({"tool_calls": [call(args="", call_id=None)]}))
        self.assertEqual((step["id"], step["args"]), ("call_0", {}))

    def test_only_first_of_several_calls_is_used(self):
        calls = [call("a", call_id="1"), call("b", call_id="2")]
        self.assertEqual(parse(reply({"tool_calls": calls}))["name"], "a")

    def test_tool_call_wins_over_text(self):
        step = parse(reply({"content": "let me check", "tool_calls": [call()]}))
        self.assertEqual(step["type"], "tool_call")

    def test_bad_argument_json(self):
        with self.assertRaises(LLMError):
            parse(reply({"tool_calls": [call(args="{not json")]}))

    def test_arguments_must_be_an_object(self):
        with self.assertRaises(LLMError):
            parse(reply({"tool_calls": [call(args="[1, 2]")]}))

    def test_tool_call_needs_a_name(self):
        with self.assertRaises(LLMError):
            parse(reply({"tool_calls": [call(name="")]}))

    def test_empty_answer_is_an_error(self):
        for message in ({"content": ""}, {"content": None}, {"content": "   "}):
            with self.assertRaises(LLMError):
                parse(reply(message))

    def test_malformed_reply_is_an_error(self):
        for data in ({}, {"choices": []}, {"choices": [{}]}, None):
            with self.assertRaises(LLMError):
                parse(data)


if __name__ == "__main__":
    unittest.main()
