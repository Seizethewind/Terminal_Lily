"""Turns what you type after /search into words, an optional category and an optional kind."""
import re

from lily.memory.taxonomy.paths import clean
from lily.utils.errors import LilyError

STOP = {"the", "and", "for", "are", "but", "not", "you", "with", "what", "this", "that", "have", "from",
        "your", "how", "can", "does", "was", "who", "why", "when", "where"}
MAX_WORDS = 12
ONLY = re.compile(r"\s+only\s+(chats|notes|words)\s*$", re.I)
IN = re.compile(r"\s+in\s+(\S+)\s*$", re.I)


def words(text):
    """The lowercase words worth searching for, without repeats."""
    found = []
    for word in re.findall(r"\w+", text.lower()):
        if len(word) > 1 and word not in STOP and word not in found:
            found.append(word)
    return found[:MAX_WORDS]


def parse(text, tree):
    """'elden ring in study/entertainment only chats' -> ('elden ring', 'study/entertainment', 'chats').
    The ending 'in <path>' only counts when the path is in the taxonomy."""
    text, kind = text.strip(), ""
    only = ONLY.search(text)
    if only:
        text, kind = text[:only.start()], only.group(1).lower()
    found, path = IN.search(text), ""
    if found:
        try:
            path = tree.resolve(clean(found.group(1)))
        except LilyError:
            path = ""
        if path and tree.has(path):
            text = text[:found.start()]
        else:
            path = ""
    return text.strip(), path, kind
