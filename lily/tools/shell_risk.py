"""Which shell commands even full autonomy still asks about.

Deleting, installs, network tools, secrets, variables (they can leak keys) and anything
that points outside the workplace. Best effort: a script run by python can still do anything.
"""
import re
import shlex

from lily.tools import shell_safety
from lily.tools.secrets import is_secret
from lily.utils.paths import in_workplace, workplace

RISKY = {
    "rm", "rmdir", "shred", "truncate", "unlink", "sudo", "su", "dd", "mkfs", "chmod", "chown",
    "kill", "killall", "pkill", "shutdown", "reboot", "curl", "wget", "ssh", "scp", "sftp", "nc",
    "ncat", "telnet", "ftp", "pip", "pip3", "pkg", "apt", "apt-get", "npm", "npx", "yarn", "gem",
    "cargo", "sh", "bash", "zsh", "eval", "exec", "source", "env", "printenv", "export", "set",
}
GIT_OK = {"status", "log", "diff", "show", "add", "commit", "init", "branch"}


def outside(path):
    """True if `path`, as Lily would open it (symlinks followed), is outside the workplace."""
    resolved = in_workplace(path)
    return resolved != workplace() and workplace() not in resolved.parents


def _outside(word):
    """True if a path-looking word points outside the workplace."""
    if not word or word.startswith("-"):
        return False
    if not (word.startswith(("/", "~")) or ".." in word.split("/")):
        return False
    return outside(word)


def reaches_outside(command):
    """True if any word of a command points outside the workplace, even for a plain read."""
    for part in re.split(r"[;&|\n]+", str(command)):
        try:
            words = shlex.split(part)
        except ValueError:
            return True
        if any(_outside(word.lstrip("<>")) for word in words[1:]):
            return True
    return False


def _risky(words):
    head = words[0]
    if head in RISKY or "=" in head:
        return True
    if head == "git" and (len(words) < 2 or words[1] not in GIT_OK):
        return True
    cleaned = [word.lstrip("<>") for word in words[1:]]
    return any(is_secret(word) or _outside(word) for word in cleaned if not word.startswith("-"))


def is_risky(command):
    text = str(command)
    for noise in shell_safety.NOISE:
        text = text.replace(noise, "")
    if "$" in text or "`" in text:
        return True
    for part in re.split(r"[;&|\n]+", text):
        try:
            words = shlex.split(part)
        except ValueError:
            return True
        if words and _risky(words):
            return True
    return False
