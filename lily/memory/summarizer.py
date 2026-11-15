"""Asks the model to condense recent chats into a short note."""
from lily.memory import history
from lily.state import State
from lily.utils.errors import LilyError

PROMPT = (
    "Summarize the conversation below in at most 6 short bullet points. Keep facts, decisions "
    "and the user's preferences. Reply with the bullets only."
)


def summarize(llm, pairs):
    state = State(system_prompt=PROMPT, profile="fast")
    state.add("user", history.render(pairs, width=1000)[:12000])
    result = llm.run(state)
    text = (result.get("text") or "").strip() if result.get("type") == "final" else ""
    if not text:
        raise LilyError("the model did not write a summary")
    return text
