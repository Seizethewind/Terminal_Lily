"""One cheap model call that folds new chat turns into the running summary."""
from lily.llm import parser

ASK = (
    "You keep a short memory of a user's chats with their AI companion. Update the summary below with the "
    "new chat turns. Keep what is worth remembering: decisions, plans, preferences, open tasks, names and "
    "numbers. Leave out passwords, keys and tokens. Write plain sentences, at most {limit} characters, and "
    "reply with the summary only."
)


def summarize(models, summary, turns, limit):
    """The new summary. `turns` are (id, user, answer). Keeps the old summary if the model says nothing."""
    chat = "\n".join(f"user: {user[:400]}\nLily: {answer[:400]}" for _, user, answer in turns)
    messages = [
        {"role": "system", "content": ASK.format(limit=limit)},
        {"role": "user", "content": f"Summary so far:\n{summary or '(none)'}\n\nNew chat turns:\n{chat}"},
    ]
    reply = models.chat("worker", models.tier("summarizer", chat), messages)
    text = parser.parse(reply.data).get("text", "").strip()
    return text[:limit] if text else summary
