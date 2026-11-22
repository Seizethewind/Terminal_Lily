"""Spots paths and words that point at keys, tokens and passwords."""
import fnmatch
from pathlib import PurePath

NAMES = (
    ".env*", "*.pem", "*.key", "id_rsa*", "id_ed25519*", "*token*", "*secret*",
    "*password*", "credentials*", ".netrc", ".git-credentials", "authorized_keys",
    "environ",   # /proc/<pid>/environ holds every environment variable, API keys included
    "*_history",   # shell history often holds pasted keys and passwords
    ".npmrc", ".pypirc", ".pgpass", "hosts.yml",   # hosts.yml is where the gh tool keeps its token
    "*.p12", "*.pfx", "*.kdbx",
)
FOLDERS = {".ssh", ".gnupg", ".aws", ".docker", ".kube"}
PLACES = ("/.git/config/", "/.config/gh/")   # a bare name like 'config' is too common to flag on its own


def is_secret(text):
    """True if `text` (a path or a command word) looks like it points at a secret."""
    path = PurePath(str(text).strip("\"'"))
    name = path.name.lower()
    if name.endswith(".example"):
        return False
    if any(part in FOLDERS for part in path.parts):
        return True
    if any(place in f"/{path.as_posix()}/" for place in PLACES):
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in NAMES)
