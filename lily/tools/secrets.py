"""Spots paths and words that point at keys, tokens and passwords."""
import fnmatch
from pathlib import PurePath

NAMES = (
    ".env*", "*.pem", "*.key", "id_rsa*", "id_ed25519*", "*token*", "*secret*",
    "*password*", "credentials*", ".netrc", ".git-credentials", "authorized_keys",
)
FOLDERS = {".ssh", ".gnupg", ".aws"}


def is_secret(text):
    """True if `text` (a path or a command word) looks like it points at a secret."""
    path = PurePath(str(text).strip("\"'"))
    name = path.name.lower()
    if name.endswith(".example"):
        return False
    if any(part in FOLDERS for part in path.parts):
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in NAMES)
