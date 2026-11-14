"""Turns a chat-completions reply into a step the agent loop understands.

Returns {"type": "final", "text": ...} or
        {"type": "tool_call", "id": ..., "name": ..., "args": {...}}.
If the model asks for several tools at once, only the first is used; the
model can ask for the rest on its next step.
"""
import json

from lily.utils.errors import LLMError


def parse(data):
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as err:
        raise LLMError("unexpected reply format from the router") from err
    calls = message.get("tool_calls") or []
    if calls:
        return _tool_call(calls[0])
    text = (message.get("content") or "").strip()
    if not text:
        raise LLMError("the model returned an empty answer")
    return {"type": "final", "text": text}


def _tool_call(call):
    fn = call.get("function") or {}
    name = fn.get("name") or ""
    if not name:
        raise LLMError("the model asked for a tool without a name")
    raw = fn.get("arguments") or "{}"
    try:
        args = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError as err:
        raise LLMError(f"bad tool arguments from the model: {raw!r}") from err
    if not isinstance(args, dict):
        raise LLMError(f"tool arguments must be an object, got: {raw!r}")
    return {"type": "tool_call", "id": call.get("id") or "call_0", "name": name, "args": args}
