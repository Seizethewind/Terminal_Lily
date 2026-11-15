"""Recent conversation, read back from the run log."""
from lily.memory import run_log


def exchanges(db, limit=10):
    """[(question, answer), ...] oldest first, leaving out failed turns."""
    runs = run_log.recent(db, limit)
    return [(r["user_text"], r["answer"]) for r in reversed(runs) if r["answer"] and not r["error"]]


def render(pairs, width=300):
    def short(text):
        text = " ".join(text.split())
        return text if len(text) <= width else text[:width] + "..."
    return "\n".join(f"you> {short(q)}\nlily> {short(a)}" for q, a in pairs)
