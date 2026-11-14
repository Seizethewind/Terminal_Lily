"""The one interface every sub orchestrator (llm, tools, rag) follows.

Each sub orchestrator module exposes `register(lily)`, which creates the
sub orchestrator and calls `lily.register(sub)`.

What `run` takes and returns, per layer:
  llm.run(state)               -> {"type": "final", "text": str}
                               or {"type": "tool_call", "id": str,
                                   "name": str, "args": dict}
  tools.run(state, call=dict)  -> str (the tool's output)
  rag.run(state, query=str)    -> None (appends snippets to state.context)
"""
from typing import Protocol


class SubOrchestrator(Protocol):
    name: str

    def run(self, state, **kwargs):
        """Do this layer's job for the current step."""
