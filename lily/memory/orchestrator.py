"""Data layer sub orchestrator: records every turn and turns your verdicts into learning."""
from lily.memory import export_dataset, feedback, history, lessons, profile_hints, run_log, summarizer
from lily.memory.code_taxonomy import CodeTaxonomy
from lily.memory.db import Database
from lily.utils.errors import LilyError

DB_NAME = "lily.db"
DATASET_NAME = "dataset.jsonl"


class MemoryOrchestrator:
    name = "memory"

    def __init__(self, lily, db=None):
        self.lily = lily
        self._db = db
        self.last_run_id = None
        self.code = CodeTaxonomy(lambda: self.db)   # the coding taxonomy

    @property
    def db(self):
        """Opened on first use, so a broken database cannot stop Lily from starting."""
        if self._db is None:
            self._db = Database(self.lily.settings.data_dir / DB_NAME)
        return self._db

    def _layer(self, name):
        sub = self.lily.router.get(name)
        if sub is None:
            raise LilyError(f"the {name} layer is not installed")
        return sub

    def run(self, state, record=None, **kwargs):
        """Store one finished turn. `record` comes from the main orchestrator."""
        if record is None:
            return
        llm = self.lily.router.get("llm")
        record.setdefault("profile", getattr(llm, "last_profile", ""))
        record.setdefault("routed_via", getattr(llm, "last_routed_via", ""))
        self.last_run_id = run_log.record(self.db, record)
        try:
            self.code.index_run(self.last_run_id, record.get("user_text", ""), record.get("answer", ""))
        except LilyError:
            pass   # the code index is a bonus; the run itself is already saved

    def suggest_profile(self, text):
        try:
            return profile_hints.suggest(self.db, text)
        except LilyError:
            return None   # learning is a bonus; it must never break an answer

    def rate(self, rating, note=""):
        if self.last_run_id is None:
            raise LilyError("nothing to rate yet: ask me something first")
        feedback.rate(self.db, self.last_run_id, rating, note)
        return "noted as good, thanks" if rating > 0 else "noted as bad, thanks"

    def lesson(self, text, kind="lesson"):
        """Save a lesson or summary and index it, so it comes back when it is relevant."""
        number = lessons.add(self.db, text, kind)
        rag = self.lily.router.get("rag")
        try:
            if rag is not None:
                rag.remember(f"{kind}:{number}", text)
        except LilyError:
            return f"saved {kind} #{number}, but could not index it for search"
        return f"saved {kind} #{number}"

    def describe_lessons(self):
        rows = lessons.all_lessons(self.db)
        return "\n".join(f"#{n} [{kind}] {text}" for n, kind, text in rows) or "no lessons yet. Try /lesson <text>"

    def unlearn(self, number):
        item = lessons.get(self.db, number)
        if item is None:
            return f"no lesson #{number}"
        lessons.remove(self.db, number)
        rag = self.lily.router.get("rag")
        if rag is not None:
            rag.forget(f"{item[1]}:{number}")
        return f"removed {item[1]} #{number}"

    def history(self, count=10):
        return history.render(history.exchanges(self.db, count)) or "no history yet"

    def summarize(self, count=20):
        pairs = history.exchanges(self.db, count)
        if not pairs:
            raise LilyError("nothing to summarize yet")
        return self.lesson(summarizer.summarize(self._layer("llm"), pairs), kind="summary")

    def export(self, only_good=True):
        path = self.lily.settings.data_dir / DATASET_NAME
        count = export_dataset.export(self.db, path, only_good)
        return f"wrote {count} chat(s) to {path}" + ("" if count or not only_good else " (rate answers with /good)")

    def stats(self):
        rows = run_log.stats(self.db)
        return "\n".join(f"{p or '?':<6} runs {n:<4} good {g:<3} bad {b}" for p, n, g, b in rows) or "no runs yet"


def register(lily):
    lily.register(MemoryOrchestrator(lily))
