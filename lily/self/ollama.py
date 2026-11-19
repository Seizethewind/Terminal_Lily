"""The local fallback: Ollama, started when needed, with its models kept in data/models."""
import atexit
import os
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from lily.llm.providers.openai_compat import OpenAICompat
from lily.utils.errors import LLMError
from lily.utils.paths import DATA_DIR


class LocalProvider(OpenAICompat):
    """An Ollama endpoint. If nothing answers on its address, it runs `ollama serve` first."""

    def __init__(self, base_url, api_key="", timeout=60, models_dir=None, start_wait=60, popen=subprocess.Popen):
        super().__init__(base_url, api_key, timeout)
        self.host = urlparse(base_url).netloc
        self.models_dir = models_dir or DATA_DIR / "models"
        self.start_wait, self.popen, self.proc = start_wait, popen, None
        atexit.register(self.stop)

    def up(self):
        try:
            urllib.request.urlopen(f"http://{self.host}/", timeout=2).close()
        except urllib.error.HTTPError:
            return True   # it answered, just not with 200
        except OSError:
            return False
        return True

    def start(self):
        env = {**os.environ, "OLLAMA_MODELS": str(self.models_dir), "OLLAMA_HOST": self.host}
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.proc = self.popen(["ollama", "serve"], env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as err:
            raise LLMError(f"cannot start ollama: {err}") from err
        deadline = time.monotonic() + self.start_wait
        while time.monotonic() < deadline:
            if self.up():
                return
            if self.proc.poll() is not None:
                raise LLMError("ollama stopped right after starting")
            time.sleep(1)
        raise LLMError(f"ollama did not answer within {self.start_wait} seconds")

    def chat(self, payload):
        if not self.up():
            self.start()
        reply = super().chat(payload)
        reply.routed_via = reply.routed_via or payload.get("model", "local")
        return reply

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
