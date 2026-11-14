"""LLM sub orchestrator: pick a profile, call the router, parse the answer."""
from lily.llm import parser, profile_picker, prompt_builder
from lily.llm.providers.openai_compat import OpenAICompat
from lily.utils.logger import get_logger

log = get_logger("llm")


class LLMOrchestrator:
    name = "llm"

    def __init__(self, lily, provider=None):
        self.lily = lily
        settings = lily.settings
        self.provider = provider or OpenAICompat(
            settings.base_url, settings.api_key, settings.timeout
        )
        self.last_routed_via = ""   # which model really answered (for the run log)

    def run(self, state, **kwargs):
        profiles = self.lily.settings.profiles
        key = profile_picker.pick(state, self.lily.settings.rules)
        if key not in profiles:
            key = state.profile
        payload = prompt_builder.build(profiles[key], state.view(), self._tool_schemas())
        reply = self.provider.chat(payload)
        self.last_routed_via = reply.routed_via
        log.info("profile=%s model=%s served_by=%s", key, profiles[key], reply.routed_via or "?")
        return parser.parse(reply.data)

    def _tool_schemas(self):
        schemas = getattr(self.lily.router.get("tools"), "schemas", None)
        return schemas() if callable(schemas) else None


def register(lily):
    lily.register(LLMOrchestrator(lily))
