"""The think -> act -> observe loop for one user message."""
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("agent")
NO_LLM = "My LLM layer isn't installed yet, so I can't answer. It arrives in the next update."


class AgentLoop:
    def __init__(self, router, max_steps=8):
        self.router = router
        self.max_steps = max_steps
        self.last = {"tools": [], "steps": 0}   # what the latest turn did (for the run log)

    def run(self, state, user_text):
        self.last = {"tools": [], "steps": 0}
        state.trim()
        state.context.clear()
        state.add("user", user_text)
        self._recall(state, user_text)
        for _ in range(self.max_steps):
            llm = self.router.get("llm")
            if llm is None:
                return NO_LLM
            result = llm.run(state)
            self.last["steps"] += 1
            target = self.router.route(result)
            if target is None:
                text = result.get("text", "")
                state.add("assistant", text)
                return text
            self.last["tools"].append(result.get("name", ""))
            state.add_tool_call(result)
            state.add_tool_result(result, self._act(target, state, result))
        return f"I stopped after {self.max_steps} steps without a final answer."

    def _recall(self, state, query):
        rag = self.router.get("rag")
        if rag is None:
            return
        try:
            rag.run(state, query=query)
        except LilyError as err:
            log.warning("rag failed: %s", err)

    def _act(self, target, state, call):
        sub = self.router.get(target)
        if sub is None:
            return f"Error: the {target} layer is not installed."
        try:
            return str(sub.run(state, call=call))
        except LilyError as err:
            log.warning("%s failed: %s", target, err)
            return f"Error: {err}"
