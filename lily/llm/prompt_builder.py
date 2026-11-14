"""Builds the chat-completions request body."""


def build(model, messages, tool_schemas=None):
    payload = {"model": model, "messages": messages}
    if tool_schemas:
        payload["tools"] = tool_schemas
    return payload
