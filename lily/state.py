"""Conversation state: the messages the model will see."""
import json


class State:
    def __init__(self, system_prompt="", profile="auto", max_history=40):
        self.system_prompt = system_prompt
        self.profile = profile
        self.max_history = max_history
        self.context = []   # RAG snippets for the current turn
        self.messages = []

    def add(self, role, content, **extra):
        self.messages.append({"role": role, "content": content, **extra})

    def add_tool_call(self, call):
        fn = {"name": call["name"], "arguments": json.dumps(call.get("args", {}))}
        self.add("assistant", "", tool_calls=[{"id": call["id"], "type": "function", "function": fn}])

    def add_tool_result(self, call, output):
        self.add("tool", output, tool_call_id=call["id"])

    def view(self):
        """Messages to send to the model: system prompt, notes, then history."""
        head = []
        if self.system_prompt:
            head.append({"role": "system", "content": self.system_prompt})
        if self.context:
            notes = "Relevant notes:\n" + "\n".join(self.context)
            head.append({"role": "system", "content": notes})
        return head + self.messages

    def trim(self):
        """Keep only the newest messages, starting at a user message."""
        if len(self.messages) <= self.max_history:
            return
        tail = self.messages[-self.max_history:]
        kept = list(tail)
        while kept and kept[0]["role"] != "user":
            kept.pop(0)
        self.messages = kept or tail

    def reset(self):
        self.messages.clear()
        self.context.clear()
