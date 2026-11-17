"""Decides if a shell command only looks around and never changes anything.

Best effort: anything it does not recognise counts as a change and asks the user.
"""
import shlex

from lily.tools.secrets import is_secret

READ_ONLY = {
    "ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "find", "pwd", "whoami", "uname",
    "stat", "file", "du", "df", "basename", "dirname", "which", "realpath", "cut", "tr", "echo",
}
GIT_READ = {"status", "log", "diff", "show"}
FIND_WRITES = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls"}
BAD = (">", "<", "`", "$(", "${", ";", "&", "||", "\n", "\r")   # redirects, chaining, substitution
NOISE = ("2>/dev/null", "2>&1")   # harmless, very common


def _words_ok(words):
    if not words:
        return False
    command, rest = words[0], words[1:]
    if command == "xargs":   # fine when what it runs is fine
        return _words_ok([word for word in rest if not word.startswith("-")])
    if command == "git":
        return bool(rest) and rest[0] in GIT_READ
    if command not in READ_ONLY:
        return False
    if command == "find" and FIND_WRITES & set(rest):
        return False
    return not any(is_secret(word) for word in rest if not word.startswith("-"))


def is_read_only(command):
    text = str(command)
    for noise in NOISE:
        text = text.replace(noise, "")
    if any(bad in text for bad in BAD):
        return False
    try:
        parts = [shlex.split(part) for part in text.split("|")]
    except ValueError:
        return False
    return all(_words_ok(words) for words in parts)
