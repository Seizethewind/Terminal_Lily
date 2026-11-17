"""Category paths: 'study/history/medieval'. Lowercase words joined by '/'."""
import re

from lily.utils.errors import LilyError

SEGMENT = re.compile(r"^[a-z0-9][a-z0-9-]{0,29}$")
MAX_DEPTH = 6
UNKNOWN = "unknown"   # reserved: "looked at, does not fit anywhere yet". Always valid, never a category.


def slug(text):
    """'Data Structure' -> 'data-structure'."""
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:30].strip("-")


def clean(path):
    """Tidy and check a path: 'Study / History' -> 'study/history'."""
    parts = [slug(part) for part in str(path).strip().strip("/").split("/")]
    if not all(SEGMENT.match(part) for part in parts) or len(parts) > MAX_DEPTH:
        raise LilyError(
            f"'{path}' is not a category path: use 1 to {MAX_DEPTH} words joined by '/', like study/history")
    return "/".join(parts)


def parent(path):
    """'a/b/c' -> 'a/b'. A top-level path has the parent ''."""
    return path.rpartition("/")[0]


def ancestors(path):
    """'a/b/c' -> ['a', 'a/b']."""
    parts = path.split("/")
    return ["/".join(parts[:count]) for count in range(1, len(parts))]


def is_unknown(path):
    return path == UNKNOWN or path.startswith(UNKNOWN + "/")
