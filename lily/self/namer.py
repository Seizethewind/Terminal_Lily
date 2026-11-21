"""A short title for a task, from one cheap model call."""
from lily.llm import parser

ASK = "Give the task below a title of at most six words. Reply with the title only, no quotes."


def make_title(models, task):
    """The title, or '' when the model says nothing usable."""
    messages = [{"role": "system", "content": ASK}, {"role": "user", "content": task[:1500]}]
    reply = models.chat("worker", models.tier("namer", task), messages)
    lines = parser.parse(reply.data).get("text", "").strip().splitlines()
    return lines[0].strip(" \"'.*#-")[:60] if lines else ""
