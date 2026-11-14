import unittest

from lily.state import State


class StateTests(unittest.TestCase):
    def test_view_puts_system_prompt_and_notes_first(self):
        state = State("be nice")
        state.context.append("note A")
        state.add("user", "hi")
        roles = [m["role"] for m in state.view()]
        self.assertEqual(roles, ["system", "system", "user"])

    def test_view_without_prompt_has_only_messages(self):
        state = State("")
        state.add("user", "hi")
        self.assertEqual(len(state.view()), 1)

    def test_tool_call_and_result_are_linked(self):
        state = State()
        call = {"id": "c1", "name": "shell", "args": {"cmd": "ls"}}
        state.add_tool_call(call)
        state.add_tool_result(call, "file.txt")
        self.assertEqual(state.messages[0]["tool_calls"][0]["id"], "c1")
        self.assertEqual(state.messages[1]["tool_call_id"], "c1")

    def test_trim_keeps_newest_and_starts_at_user(self):
        state = State(max_history=3)
        for i in range(4):
            state.add("user", f"q{i}")
            state.add("assistant", f"a{i}")
        state.trim()
        self.assertEqual(state.messages[0]["role"], "user")
        self.assertEqual(state.messages[-1]["content"], "a3")
        self.assertLessEqual(len(state.messages), 3)

    def test_reset_clears_everything(self):
        state = State()
        state.add("user", "x")
        state.context.append("n")
        state.reset()
        self.assertEqual((state.messages, state.context), ([], []))


if __name__ == "__main__":
    unittest.main()
