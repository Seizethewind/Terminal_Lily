"""Template for a worker: a role, a model tier and a task, run by its own agent loop and state.

kind 'worker' asks the workers' router first; kind 'lily' (a takeover) asks Lily's router first.
`kit` is the self orchestrator: it has .cfg, .models (ModelRouter) and .hive.
`done` holds the results of earlier steps of the same task.
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
        self.task = task
        self.tier = kit.models.tier(role, task) if kind == "worker" else "heavy"
        tools = WorkerTools(lily, kit.hive, task_id, kit.cfg.limits["approval_wait"])
        router = Router()   # its own small router: the worker's LLM and the worker's tools
        router.register(WorkerLLM(kit.models, self.tier, tools, kind))
        router.register(tools)
        self.loop = AgentLoop(router, kit.cfg.limits["worker_steps"])
        self.state = State(personality.worker_prompt(role, task, notes, done), profile="worker")

    def run(self):
        answer = self.loop.run(self.state, self.task)
        if answer.startswith(GAVE_UP):
            raise LilyError("ran out of steps before finishing")
        return answer
