import unittest

from lily.orchestrator import Lily
from lily.tools.builtin.rag_search import Tool
from lily.utils.errors import ToolError
from tests.fakes import make_settings


class FakeRag:
    name = "rag"

    def __init__(self, hits):
        self.hits, self.asked = hits, []

    def search(self, query, limit):
        self.asked.append((query, limit))
        return self.hits


def tool_with(rag=None):
    lily = Lily(make_settings())
    if rag:
        lily.register(rag)
    return Tool(lily)


class RagSearchTests(unittest.TestCase):
    def test_passages_are_joined(self):
        rag = FakeRag(["first note", "second note"])
        out = tool_with(rag).execute({"query": "cats", "limit": "3"})
        self.assertEqual(out, "first note\n---\nsecond note")
        self.assertEqual(rag.asked, [("cats", 3)])

    def test_default_limit(self):
        rag = FakeRag(["x"])
        tool_with(rag).execute({"query": "dogs"})
        self.assertEqual(rag.asked, [("dogs", 5)])

    def test_no_hits(self):
        self.assertEqual(tool_with(FakeRag([])).execute({"query": "x"}), "no matching notes found")

    def test_missing_rag_layer_is_explained(self):
        with self.assertRaisesRegex(ToolError, "not installed yet"):
            tool_with().execute({"query": "x"})


if __name__ == "__main__":
    unittest.main()
