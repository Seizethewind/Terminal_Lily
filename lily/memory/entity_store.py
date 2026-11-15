"""Reads and writes the entity tables: your own words and the mentions found in chats."""


def terms(db):
    """[(word, class, subclass)] you added yourself."""
    return db.rows("SELECT name, cls, sub FROM entity_terms ORDER BY name")


def add_term(db, word, cls, sub):
    db.write("DELETE FROM entity_terms WHERE name = ?", (word,))
    db.write("INSERT INTO entity_terms(name, cls, sub) VALUES (?, ?, ?)", (word, cls, sub))


def remove_term(db, word):
    db.write("DELETE FROM entity_terms WHERE name = ?", (word,))


def save(db, run_id, found, words):
    """Replace the mentions of one chat. found = {word: count}, words = {word: (class, sub)}."""
    db.write("DELETE FROM entity_mentions WHERE run_id = ?", (run_id,))
    for word, count in found.items():
        if word in words:
            cls, sub = words[word]
            db.write(
                "INSERT INTO entity_mentions(run_id, name, cls, sub, count) VALUES (?, ?, ?, ?, ?)",
                (run_id, word, cls, sub, count),
            )


def summary(db):
    """[(class, subclass, word, mentions, chats)] grouped, most mentioned first."""
    return db.rows(
        "SELECT cls, sub, name, SUM(count), COUNT(DISTINCT run_id) FROM entity_mentions "
        "GROUP BY cls, sub, name ORDER BY cls, sub, SUM(count) DESC, name"
    )


def chats(db, word, limit=5):
    """[(run_id, user_text)] newest first."""
    return db.rows(
        "SELECT r.id, r.user_text FROM entity_mentions m JOIN runs r ON r.id = m.run_id "
        "WHERE m.name = ? ORDER BY r.id DESC LIMIT ?", (word, limit),
    )
