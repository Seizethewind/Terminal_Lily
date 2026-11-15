"""Chooses which router profile (auto / fast / smart) a turn should use.

Rules for now: a profile you set by hand always wins. While the profile is
"auto", trigger words from models.toml may switch to fast or smart. If none
match, `suggest` (the memory layer, learning from /good and /bad) may pick one.
"""
import re


def _last_user_text(state):
    for message in reversed(state.messages):
        if message["role"] == "user":
            return message["content"]
    return ""


def _mentions(text, word):
    """True if a word in text starts with `word` (so 'plan' matches 'planning')."""
    return re.search(r"\b" + re.escape(word), text) is not None


def pick(state, rules, suggest=None):
    if state.profile != "auto":
        return state.profile
    text = _last_user_text(state).lower()
    for profile, words in rules.items():
        if any(_mentions(text, word.lower()) for word in words):
            return profile
    return (suggest(text) if suggest else None) or "auto"
