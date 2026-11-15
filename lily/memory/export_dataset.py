"""Writes your chats as a JSONL training set (one chat per line, chat-messages format)."""
import json
from pathlib import Path

from lily.utils.errors import LilyError


def export(db, path, only_good=True):
    """Write finished chats to `path`. Returns how many were written."""
    sql = ("SELECT r.user_text, r.answer, r.profile, r.routed_via, r.tools, f.rating FROM runs r "
           "LEFT JOIN feedback f ON f.run_id = r.id WHERE r.answer != '' AND r.error = '' ")
    rows = db.rows(sql + ("AND f.rating > 0 " if only_good else "") + "ORDER BY r.id")
    lines = []
    for question, answer, profile, routed_via, tools, rating in rows:
        messages = [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
        lines.append(json.dumps({
            "messages": messages, "profile": profile, "routed_via": routed_via,
            "tools": json.loads(tools or "[]"), "rating": rating,
        }, ensure_ascii=False))
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    except OSError as err:
        raise LilyError(f"cannot write {path}: {err}") from err
    return len(lines)
