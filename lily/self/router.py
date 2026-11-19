"""Model router: picks the tier and model for a job and tries the other router if one fails.

Not the same as lily/router.py, which only decides which sub orchestrator acts next.
"""
import time

from lily.llm import prompt_builder
from lily.llm.providers.openai_compat import OpenAICompat
from lily.self.ollama import LocalProvider
from lily.utils.errors import LLMError
from lily.utils.logger import get_logger

log = get_logger("self.router")
TIERS = ("light", "normal", "heavy")
ORDER = {"worker": ("workers", "lily", "local"), "lily": ("lily", "workers", "local")}   # local is the last resort


class ModelRouter:
    def __init__(self, cfg, providers=None, clock=time.monotonic):
        self.cfg = cfg
        self.clock = clock
        timeout = cfg.limits["timeout"]
        self.providers = providers or {
            name: (LocalProvider if name == "local" else OpenAICompat)(ep["url"], ep["key"], ep["timeout"] or timeout)
            for name, ep in cfg.endpoints.items()
        }
        self.fails = dict.fromkeys(self.providers, 0)
        self.paused = dict.fromkeys(self.providers, 0.0)
        self.busy = 0   # workers running now; the dispatcher keeps this up to date

    def tier(self, role, task=""):
        """Light, normal or heavy: the role's usual tier, moved by task size and by how busy we are."""
        usual = self.cfg.roles.get(role, self.cfg.roles["default"])
        index = TIERS.index(usual) if usual in TIERS else 1
        if len(task) > 1500:
            index = min(index + 1, 2)
        if self.busy >= self.cfg.limits["max_workers"]:
            index = max(index - 1, 0)
        return TIERS[index]

    def model(self, tier):
        return self.cfg.tiers[tier]

    def chat(self, kind, tier, messages, tools=None, model=None):
        """Ask the first router for `kind` ('worker' or 'lily'); if it fails, try the next, local last."""
        errors = []
        for name in ORDER[kind]:
            if name not in self.providers:
                continue
            if self.clock() < self.paused[name]:
                errors.append(f"{name}: paused after repeated failures")
                continue
            ours = self.cfg.endpoints.get(name, {}).get("model")   # a router may need its own model name
            payload = prompt_builder.build(ours or model or self.model(tier), messages, tools)
            try:
                reply = self.providers[name].chat(payload)
            except LLMError as err:
                self._failed(name, err)
                errors.append(f"{name}: {err}")
                continue
            self.fails[name] = 0
            return reply
        raise LLMError("no router could answer: " + "; ".join(errors))

    def _failed(self, name, err):
        self.fails[name] += 1
        log.warning("router %s failed (%d in a row): %s", name, self.fails[name], err)
        if self.fails[name] >= self.cfg.limits["breaker_fails"]:
            self.paused[name] = self.clock() + self.cfg.limits["breaker_pause"]
            self.fails[name] = 0
