"""Finds the known words of the entity taxonomy inside a text (code is ignored)."""
import re
from collections import Counter

CODE = re.compile(r"^```.*?^```[ \t]*$|`[^`\n]*`", re.M | re.S)


def build(words):
    """One pattern for all words, longest first so 'new york' wins over a shorter match."""
    if not words:
        return None
    body = "|".join(re.escape(word) for word in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<!\w)({body})(?:e?s)?(?!\w)", re.I)   # also finds plurals: dog, dogs


def find(pattern, text):
    """{word: how many times}, lowercase."""
    if pattern is None or not text:
        return {}
    return dict(Counter(m.group(1).lower() for m in pattern.finditer(CODE.sub(" ", text))))
