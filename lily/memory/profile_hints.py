"""Learns from your /good and /bad which profile (fast or smart) suits a kind of question."""
import re

MIN_OVERLAP = 2   # long words a past question must share with the new one
MIN_VOTES = 2     # agreeing past verdicts needed before Lily changes her pick
WINDOW = 300      # how many past verdicts are looked at


def _words(text):
    return {word for word in re.findall(r"\w+", text.lower()) if len(word) >= 4}


def suggest(db, text):
    """'fast', 'smart' or None. Good answers vote for the profile that gave them.

    A bad answer from fast or auto votes for smart (a bad smart answer says nothing).
    """
    mine = _words(text)
    if len(mine) < MIN_OVERLAP:
        return None
    votes = {"fast": 0, "smart": 0}
    rows = db.rows(
        "SELECT r.user_text, r.profile, f.rating FROM feedback f JOIN runs r ON r.id = f.run_id "
        "ORDER BY f.id DESC LIMIT ?", (WINDOW,),
    )
    for past_text, profile, rating in rows:
        if len(mine & _words(past_text)) < MIN_OVERLAP:
            continue
        if rating > 0 and profile in votes:
            votes[profile] += 1
        elif rating < 0 and profile in ("fast", "auto"):
            votes["smart"] += 1
    best = max(votes, key=votes.get)
    other = "fast" if best == "smart" else "smart"
    return best if votes[best] >= MIN_VOTES and votes[best] > votes[other] else None
