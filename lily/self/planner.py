"""Turns a task into a short list of numbered steps with one cheap model call."""
import re

from lily.llm import parser

ASK = (
    "Break the task into at most {limit} short numbered steps, one per line, like '1. do this'. "
    "No code and no explanations. If the task is simple, give a single step."
)
LINE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")


def parse_steps(text, limit):
    matches = (LINE.match(line) for line in str(text).splitlines())
    return [match.group(1) for match in matches if match][:limit]


def make_plan(models, task, limits, role="planner"):
    """The steps for `task`; just the task itself when it is short or planning does not work."""
    if len(task) < limits["plan_min_chars"]:
        return [task]
    messages = [
        {"role": "system", "content": ASK.format(limit=limits["max_plan_steps"])},
        {"role": "user", "content": task},
    ]
    try:
        reply = models.chat("worker", models.tier(role, task), messages)
        steps = parse_steps(parser.parse(reply.data).get("text", ""), limits["max_plan_steps"])
    except Exception:   # noqa: BLE001 - planning is a bonus, never a reason to fail
        return [task]
    return steps if len(steps) > 1 else [task]
