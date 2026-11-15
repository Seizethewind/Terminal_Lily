"""The one interface every sub orchestrator (llm, tools, rag) follows.

Each sub orchestrator module exposes `register(lily)`, which creates the
sub orchestrator and calls `lily.register(sub)`.

What `run` takes and returns, per layer:
  llm.run(state)               -> {"type": "final", "text": str}
                               or {"type": "tool_call", "id": str,
                                   "name": str, "args": dict}
  tools.run(state, call=dict)  -> str (the tool's output)
  tools.schemas()              -> list of OpenAI-style tool definitions
                                  (optional; the llm layer offers them to the model)
  tools.describe() / tools.reload() -> str (used by /tools and /reload)
  rag.run(state, query=str)    -> None (appends snippets to state.context)
  rag.search(query, limit)     -> list[str] (used by the rag_search tool)
  rag.ingest(path) / describe() / forget(source) -> str (used by /ingest /notes /forget)
  rag.remember(source, text)   -> None (index text, e.g. a lesson, under a source name)
  memory.run(state, record=dict) -> None (stores one finished turn in the run log)
  memory.suggest_profile(text) -> "fast" | "smart" | None (learned from /good and /bad)
  llm.last_profile / llm.last_routed_via -> what the latest llm call used (for the run log)
"""
from typing import Protocol


class SubOrchestrator(Protocol):
    name: str

    def run(self, state, **kwargs):
        """Do this layer's job for the current step."""
