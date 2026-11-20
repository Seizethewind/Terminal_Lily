"""Template for a worker: a role, a model tier and a task, run by its own agent loop and state.

kind 'worker' asks the workers' router first; kind 'lily' (a takeover) asks Lily's router first.
`kit` is the self orchestrator: it has .cfg, .models (ModelRouter) and .hive.
`done` holds the results of earlier steps of the same task.
A failed attempt is undone (staged files and command changes) before the error goes on.
"""
from lily.agent_loop import AgentLoop
from lily.router import Router
from lily.self import personality
from lily.self.worker_llm import WorkerLLM
from lily.self.worker_tools import WorkerTools
from lily.state import State
from lily.utils.errors import LilyError

GAVE_UP = "I stopped after"   # what AgentLoop answers when it runs out of steps


class SubAgent:
    def __init__(self, lily, kit, task_id, role, task, kind="worker", notes=(), done=()):
        self.task, self.hive, self.task_id = task, kit.hive, task_id
        self.tier = kit.models.tier(role, task) if kind == "worker" else "heavy"
        self.tools = WorkerTools(lily, kit.hive, task_id, kit.cfg.limits["approval_wait"], kit.cfg.limits)
        router = Router()   # its own small router: the worker's LLM and the worker's tools
        router.register(WorkerLLM(kit.models, self.tier, self.tools, kind))
        router.register(self.tools)
        self.loop = AgentLoop(router, kit.cfg.limits["worker_steps"])
        self.state = State(personality.worker_prompt(role, task, notes, done), profile="worker")

    def run(self):
        try:
            answer = self.loop.run(self.state, self.task)
            if answer.startswith(GAVE_UP):
                raise LilyError("ran out of steps before finishing")
        except Exception:
            undone = self.tools.undo()
            if undone:
                self.hive.note(self.task_id, f"attempt undone: {undone}")
            raise
        self.tools.finish()
        return answer
