"""Reads and writes the code_blocks table (the coding taxonomy's data)."""
COLUMNS = "run_id, source, language, grp, family, known, guessed, lines, code"


def save(db, run_id, blocks):
    """Replace the blocks of one chat (so scanning twice never duplicates)."""
    db.write("DELETE FROM code_blocks WHERE run_id = ?", (run_id,))
    for b in blocks:
        db.write(
            f"INSERT INTO code_blocks({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, b["source"], b["language"], b["group"], b["family"], int(b["known"]),
             int(b["guessed"]), b["lines"], b["code"]),
        )


def summary(db):
    """[(language, group, family, known, blocks, chats), ...] biggest first."""
    return db.rows(
        "SELECT language, grp, family, known, count(*), count(DISTINCT run_id) FROM code_blocks "
        "GROUP BY language ORDER BY count(*) DESC, language"
    )


def recent(db, language, limit=5):
    """[(run_id, source, lines, code), ...] newest first."""
    return db.rows(
        "SELECT run_id, source, lines, code FROM code_blocks WHERE language = ? ORDER BY id DESC LIMIT ?",
        (language, limit),
    )


def chats_with(db, language):
    """[(user_text, answer), ...] for every chat that contains this language."""
    return db.rows(
        "SELECT r.user_text, r.answer FROM runs r WHERE r.id IN "
        "(SELECT run_id FROM code_blocks WHERE language = ?) ORDER BY r.id", (language,)
    )
