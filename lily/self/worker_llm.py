"""LLM sub orchestrator for one worker: asks the model router, then parses the answer."""
from lily.llm import parser


class WorkerLLM:
    name = "llm"

    def __init__(self, models, tier, tools, kind="worker"):
        self.models, self.tier, self.tools, self.kind = models, tier, tools, kind

    def run(self, state, **kwargs):
        reply = self.models.chat(self.kind, self.tier, state.view(), self.tools.schemas())
        return parser.parse(reply.data)
