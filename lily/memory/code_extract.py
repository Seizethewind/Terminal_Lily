"""Finds fenced code blocks in text and labels each with its language."""
import re

from lily.memory.code_guess import guess

FENCE = re.compile(r"^```[ \t]*([^\s`]*)[^\n]*\n(.*?)^```[ \t]*$", re.M | re.S)
MAX_CODE = 20_000   # characters kept per block


def extract(text, languages, source):
    """One dict per code block: language, group, family, known, guessed, lines, code, source."""
    blocks = []
    for tag, code in FENCE.findall(text or ""):
        guessed = not tag
        info = languages.resolve(tag or guess(code) or "unknown")
        if info is None:
            continue   # a tag such as 'text' or 'output': not code
        if guessed and info["language"] == "unknown":
            info = {**info, "known": False}
        code = code.rstrip("\n")
        cut = code if len(code) <= MAX_CODE else code[:MAX_CODE] + "\n[cut]"
        lines = code.count("\n") + 1 if code else 0
        blocks.append({**info, "guessed": guessed, "lines": lines, "code": cut, "source": source})
    return blocks
