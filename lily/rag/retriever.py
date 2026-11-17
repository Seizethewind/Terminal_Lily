"""Turns a question into a full-text query and returns the best passages."""
import re

STOP = {
    "the", "and", "for", "are", "but", "not", "you", "with", "what", "this", "that",
    "have", "from", "your", "how", "can", "does", "was", "who", "why", "when", "where",
}
MAX_WORDS = 12


def to_match(query):
    """'What is Termux?' -> '"what" OR "termux"'. Empty if nothing useful is left."""
    words = []
    for word in re.findall(r"\w+", query.lower()):
        if len(word) > 1 and word not in STOP and word not in words:
            words.append(word)
    return " OR ".join(f'"{word}"' for word in words[:MAX_WORDS])


def find(store, query, limit=5, sources=None):
    """Passages as text, best first, each labelled with where it came from.

    `sources` (optional) limits the search to those notes.
    """
    match = to_match(query)
    if not match or limit < 1:
        return []
    return [f"[{source}] {body}" for source, body in store.search(match, limit, sources)]
