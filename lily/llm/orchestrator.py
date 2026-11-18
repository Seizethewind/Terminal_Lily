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
        self.injected = provider is not None   # tests pass their own provider
        self.provider = provider or OpenAICompat(
            settings.base_url, settings.api_key, settings.timeout
        )
        self.last_routed_via = ""   # which model really answered (for the run log)
        self.last_profile = ""      # which profile was asked for (for the run log)

    def run(self, state, **kwargs):
        profiles = self.lily.settings.profiles
        suggest = getattr(self.lily.router.get("memory"), "suggest_profile", None)
        key = profile_picker.pick(state, self.lily.settings.rules, suggest)
        if key not in profiles:
            key = state.profile
        self.last_profile = key
        view, tools = state.view(), self._tool_schemas()
        models = None if self.injected else getattr(self.lily.router.get("self"), "models", None)
        if models:   # Lily's own router first, the workers' router as fallback (config/self.toml)
            reply = models.chat("lily", None, view, tools, model=profiles[key])
        else:
            reply = self.provider.chat(prompt_builder.build(profiles[key], view, tools))
        self.last_routed_via = reply.routed_via
        log.info("profile=%s model=%s served_by=%s", key, profiles[key], reply.routed_via or "?")
        return parser.parse(reply.data)

    def _tool_schemas(self):
        schemas = getattr(self.lily.router.get("tools"), "schemas", None)
        return schemas() if callable(schemas) else None


def register(lily):
    lily.register(LLMOrchestrator(lily))
