import tempfile
import unittest
from pathlib import Path

from lily.llm.orchestrator import LLMOrchestrator
from lily.orchestrator import Lily
from lily.rag.orchestrator import RagOrchestrator
from lily.tools.builtin.rag_search import Tool
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import FakeProvider, make_settings, text_reply


def setup():
    settings = make_settings()
    settings.data_dir = Path(tempfile.mkdtemp())
    lily = Lily(settings)
    rag = RagOrchestrator(lily)
    lily.register(rag)
    notes = settings.data_dir / "notes"
    notes.mkdir()
    (notes / "pets.md").write_text("Lily's cat is called Mochi.\n\nMochi hates baths.", encoding="utf-8")
    return lily, rag, notes


class RagOrchestratorTests(unittest.TestCase):
    def test_database_is_created_lazily_in_the_data_dir(self):
        lily, rag, _ = setup()
        self.assertFalse((lily.settings.data_dir / "rag.db").exists())
        rag.search("anything")
        self.assertTrue((lily.settings.data_dir / "rag.db").exists())

    def test_run_fills_the_context_for_the_turn(self):
        lily, rag, notes = setup()
        rag.ingest(notes)
        rag.run(lily.state, query="what is the cat called?")
        self.assertEqual(len(lily.state.context), 1)
        self.assertIn("Mochi", lily.state.context[0])

    def test_messages_reach_the_model_with_the_notes(self):
        lily, rag, notes = setup()
        rag.ingest(notes)
        provider = FakeProvider(text_reply("Mochi"))
        lily.register(LLMOrchestrator(lily, provider))
        self.assertEqual(lily.handle("what is the cat called?"), "Mochi")
        system = [m["content"] for m in provider.payloads[0]["messages"] if m["role"] == "system"]
        self.assertTrue(any("Relevant notes" in text and "Mochi" in text for text in system))

    def test_an_empty_store_adds_nothing(self):
        lily, rag, _ = setup()
        rag.run(lily.state, query="cat")
        self.assertEqual(lily.state.context, [])

    def test_rag_search_tool_uses_the_layer(self):
        lily, rag, notes = setup()
        rag.ingest(notes)
        out = Tool(lily).execute({"query": "baths", "limit": 1})
        self.assertIn("Mochi hates baths", out)

    def test_ingest_messages(self):
        _, rag, notes = setup()
        self.assertEqual(rag.ingest(notes), "indexed 1 file(s) as 1 passage(s)")
        empty = Path(tempfile.mkdtemp())
        self.assertIn("nothing to index", rag.ingest(empty))

    def test_describe_and_forget(self):
        _, rag, notes = setup()
        self.assertIn("no notes yet", rag.describe())
        rag.ingest(notes)
        source = str((notes / "pets.md").resolve())
        self.assertIn(source, rag.describe())
        self.assertEqual(rag.forget(source), "removed 1 passage(s)")
        self.assertIn("no notes from", rag.forget(source))

    def test_slash_commands(self):
        lily, _, notes = setup()
        self.assertIn("Usage", commands.run(lily, "/ingest"))
        self.assertIn("indexed 1 file(s)", commands.run(lily, f"/ingest {notes}"))
        self.assertIn("pets.md", commands.run(lily, "/notes"))
        self.assertIn("Usage", commands.run(lily, "/forget"))
        with self.assertRaisesRegex(LilyError, "rag layer is not installed"):
            commands.run(Lily(make_settings()), "/notes")


if __name__ == "__main__":
    unittest.main()
