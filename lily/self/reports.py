"""Text for task_status and /tasks: workers right now, then finished tasks."""


def status(kit):
    lines = kit.hive.snapshot()
    done = kit.tasks.completed(5)
    if done:
        lines.append("Finished tasks, newest first:")
        for row in done:
            where = kit.steps.progress(row[0]) if row[3] == "failed" else ""
            lines.append(kit.tasks.line(row) + (f" [{where}]" if where else ""))
    return "\n".join(lines) or "No workers running and no finished tasks yet."
