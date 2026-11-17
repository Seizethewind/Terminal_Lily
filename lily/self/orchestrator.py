"""Self sub orchestrator: Lily's character, memory, workers and hive mind in one place."""
from pathlib import Path

from lily.self import personality
from lily.self.chat_memory import ChatMemory
from lily.self.config import SelfConfig
from lily.self.dispatcher import Dispatcher
from lily.self.hive_mind import HiveMind
from lily.self.router import ModelRouter
from lily.self.task_completion import TaskLog
from lily.utils.errors import ConfigError
from lily.utils.logger import get_logger

log = get_logger("self")
CLIP = 300


def _cut(text):
    return text if len(text) <= CLIP else text[:CLIP] + "..."


class SelfOrchestrator:
    name = "self"

    def __init__(self, lily, cfg, data_dir):
        self.lily, self.cfg = lily, cfg
        self.memory = ChatMemory(data_dir / "chat_memory.db")
        self.tasks = TaskLog(data_dir / "tasks.db")
        self.hive = HiveMind()
        self.models = ModelRouter(cfg)
        self.dispatcher = Dispatcher(lily, self, self.tasks)

    def run(self, state, query=None, record=None, **kwargs):
        """Called by the agent loop before an answer (query) and by Lily after it (record)."""
        try:
            if record is not None:
                if record.get("answer") and not record.get("error"):
                    self.memory.save_turn(record["user_text"], record["answer"])
            else:
                personality.apply(state, self.cfg)
                state.context.extend(self._brief(query or "", state))
        except Exception:   # noqa: BLE001 - her inner life must never break the chat
            log.exception("self layer failed")
        return ""

    def _brief(self, query, state):
        """What Lily should have in mind for this message."""
        lines = []
        facts = self.memory.facts()
        if facts:
            lines += ["What you know about the user:"] + [f"- {fact}" for fact in facts]
        if len(state.messages) < 10:   # a fresh session: remind her how the last one ended
            for user, answer in self.memory.earlier(self.cfg.limits["recent_turns"]):
                lines.append(f"Earlier chat, user: {_cut(user)} | you: {_cut(answer)}")
        for user, answer in self.memory.search(query):
            lines.append(f"Remembered chat, user: {_cut(user)} | you: {_cut(answer)}")
        done = self.tasks.unseen()
        lines += ["Task finished since you last spoke: " + self.tasks.line(row) for row in done]
        self.tasks.mark_seen([row[0] for row in done])
        return lines + self.hive.snapshot()

    def delegate(self, role, task):
        task_id = self.dispatcher.submit(role.strip().lower() or "worker", task)
        return f"Task #{task_id} started in the background. Keep chatting; check it with task_status."

    def status(self):
        lines = self.hive.snapshot()
        done = self.tasks.completed(5)
        if done:
            lines += ["Finished tasks, newest first:"] + [self.tasks.line(row) for row in done]
        return "\n".join(lines) or "No workers running and no finished tasks yet."

    def approve(self, key, yes):
        if self.hive.answer(key, yes):
            return f"Approval {key}: {'approved' if yes else 'declined'}."
        return f"Approval {key} is not waiting (it may have timed out)."

    def remember(self, text):
        self.memory.add_fact(text)
        return "Saved."


def register(lily):
    try:
        cfg = SelfConfig.load()
    except ConfigError as err:
        log.warning("self layer is off: %s", err)
        return
    if not cfg.endpoints:
        log.warning("self layer is off: no router url in config/self.toml")
        return
    data_dir = Path(lily.settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    lily.register(SelfOrchestrator(lily, cfg, data_dir))
