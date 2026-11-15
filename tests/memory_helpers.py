"""Shared setup for the data layer tests."""
import tempfile
from pathlib import Path

from lily.llm.orchestrator import LLMOrchestrator
from lily.memory.orchestrator import MemoryOrchestrator
from lily.orchestrator import Lily
from lily.rag.orchestrator import RagOrchestrator
from lily.tools.base import BaseTool
from tests.fakes import FakeProvider, make_settings


class Hello(BaseTool):
    name = "hello"
    parameters = {"type": "object", "properties": {}}

    def run(self):
        return "hi there"


def setup(*replies, with_rag=True):
    settings = make_settings()
    settings.data_dir = Path(tempfile.mkdtemp())
    lily = Lily(settings)
    lily.confirm = lambda question: True
    memory = MemoryOrchestrator(lily)
    lily.register(memory)
    lily.register(LLMOrchestrator(lily, FakeProvider(*replies)))
    if with_rag:
        lily.register(RagOrchestrator(lily))
    return lily, memory
