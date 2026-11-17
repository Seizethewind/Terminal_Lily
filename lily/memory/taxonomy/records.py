"""What a label points at: a kind of record (run, note...) and its reference."""
import re

from lily.utils.errors import LilyError

KIND = re.compile(r"^[a-z][a-z0-9_-]{0,19}$")
MAX_REF = 300


def kind(text):
    text = str(text).strip().lower()
    if not KIND.match(text):
        raise LilyError(f"'{text}' is not a kind of record (use a short lowercase word, like run or note)")
    return text


def ref(text):
    text = str(text).strip()
    if not text or len(text) > MAX_REF:
        raise LilyError(f"a record reference must be 1 to {MAX_REF} characters")
    return text
