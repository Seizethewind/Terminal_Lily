"""Search Lily's own saved notes and documents (needs the RAG layer)."""
from lily.tools.base import BaseTool, to_int
from lily.utils.errors import ToolError


class Tool(BaseTool):
    name = "rag_search"
    description = "Search Lily's saved notes and documents. Returns the best matching passages."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "what to look for"},
            "limit": {"type": "integer", "description": "how many passages (default 5)"},
        },
        "required": ["query"],
    }

    def run(self, query, limit=5):
        rag = self.lily.router.get("rag")
        if rag is None or not hasattr(rag, "search"):
            raise ToolError("the notes (RAG) layer is not installed yet")
        hits = rag.search(query, to_int(limit, "limit", 5))
        return "\n---\n".join(hits) if hits else "no matching notes found"
