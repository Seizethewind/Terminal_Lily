"""Searches the chats (the runs table): ranked full-text search, or plain matching without FTS5."""
from lily.memory.search_query import words


def _full_text(db, found, glue, extra, params, limit, offset):
    tokens = [f'"{word}"' for word in found]
    tokens[-1] += "*"   # the last word may be half typed
    sql = ("SELECT r.id, r.ts, snippet(runs_fts, -1, '[', ']', '...', 14) FROM runs_fts "
           "JOIN runs r ON r.id = runs_fts.rowid WHERE runs_fts MATCH ?"
           f"{' AND ' + extra if extra else ''} ORDER BY runs_fts.rank LIMIT ? OFFSET ?")
    return db.rows(sql, [glue.join(tokens), *params, limit, offset])


def _plain(db, found, glue, extra, params, limit, offset):
    word = "instr(lower(r.user_text || ' ' || r.answer), ?) > 0"
    sql = (f"SELECT r.id, r.ts, substr(r.user_text, 1, 120) FROM runs r WHERE ({glue.join([word] * len(found))})"
           f"{' AND ' + extra if extra else ''} ORDER BY r.id DESC LIMIT ? OFFSET ?")
    return db.rows(sql, [*found, *params, limit, offset])


def find(db, text, scope=("", ()), limit=5, offset=0):
    """([(chat number, date, snippet)], whether more follow). Chats with all the words come first;
    when none has them all, chats with any of them. `scope` is store.run_filter()'s result."""
    found = words(text)
    if not found:
        return [], False
    extra, params = scope
    for glue in ("AND", "OR"):
        rows = (_full_text if db.fts else _plain)(db, found, f" {glue} ", extra, list(params), limit + 1, offset)
        if rows:
            break
    return [(run, when[:10], " ".join(str(snippet).split())) for run, when, snippet in rows[:limit]], len(rows) > limit
