"""Guesses the language of a code block that has no tag. Rough on purpose."""
import json
import re

RULES = [   # most specific first
    (r"^#!.*\bpython", "python"), (r"^#!.*\bnode", "javascript"), (r"^#!.*\b(ba|z|)sh\b", "bash"),
    (r"<\?php", "php"), (r"(?i)<!doctype html|<html\b", "html"),
    (r"std::|#include\s*<(iostream|vector|string)>", "cpp"), (r"^\s*#include\s*[<\"]", "c"),
    (r"System\.out\.print|public\s+(static\s+)?(class|void)\b", "java"),
    (r"^package \w+$|^func (\(\w+ \*?\w+\) )?\w+\(", "go"),
    (r"^\s*fn \w+.*\{|\blet mut\b|println!\(", "rust"),
    (r"\binterface \w+ \{|: (string|number|boolean)\b.*[=;)]", "typescript"),
    (r"\b(const|let) \w+ = |console\.log\(|=> \{|\bfunction \w*\(", "javascript"),
    (r"^\s*def \w+\(.*\)\s*(->.*)?:\s*$|^(from [\w.]+ )?import [\w., ]+$", "python"),
    (r"(?i)^\s*(select\s.+\sfrom|insert into|create table|update \w+ set)\b", "sql"),
    (r"^\s*(\$ |sudo |pkg |apt |pip |npm |git |cd |mkdir |export )", "bash"),
    (r"^\s*[.#]?[\w-]+\s*\{[^}]*:\s*[^}]*;", "css"),
]


def guess(code):
    """A language name, or '' when nothing matches."""
    stripped = code.strip()
    if stripped[:1] in "{[":
        try:
            json.loads(stripped)
            return "json"
        except ValueError:
            pass
    for pattern, language in RULES:
        if re.search(pattern, code, re.M):
            return language
    return ""
