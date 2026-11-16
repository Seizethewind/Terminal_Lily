"""RAG sub orchestrator: find notes for a question, and manage what is indexed."""
from lily.rag import ingest, retriever
from lily.rag.chunker import chunk
from lily.rag.store import Store

DB_NAME = "rag.db"
TOP = 3   # passages added to the prompt for each message


class RagOrchestrator:
    name = "rag"

    def __init__(self, lily, store=None):
        self.lily = lily
        self._store = store

    @property
    def store(self):
        """Opened on first use, so a broken database cannot stop Lily from starting."""
        if self._store is None:
            self._store = Store(self.lily.settings.data_dir / DB_NAME)
        return self._store

    def run(self, state, query="", **kwargs):
        state.context.extend(retriever.find(self.store, query, TOP))

    def search(self, query, limit=5, sources=None):
        return retriever.find(self.store, query, limit, sources)

    def remember(self, source, text):
        """Index text under a source name (the data layer uses this for lessons)."""
        self.store.replace(source, chunk(text))

    def ingest(self, path):
        files, chunks = ingest.ingest(self.store, path)
        if not files:
            return "nothing to index there (no readable text files found)"
        return f"indexed {files} file(s) as {chunks} passage(s)"

    def describe(self):
        rows = self.store.sources()
        if not rows:
            return "no notes yet. Use /ingest <file or folder>"
        return "\n".join(f"{count:>4}  {source}" for source, count in rows)

    def forget(self, source):
        removed = self.store.forget(source)
        return f"removed {removed} passage(s)" if removed else f"no notes from {source}"


def register(lily):
    lily.register(RagOrchestrator(lily))
