"""Provider for any OpenAI-compatible /chat/completions endpoint (your router).

Uses only the standard library, so there is nothing extra to install on Termux.
"""
import json
import urllib.error
import urllib.request

from lily.llm.base import Reply
from lily.utils.errors import LLMError


class OpenAICompat:
    def __init__(self, base_url, api_key="", timeout=60):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, payload):
        headers = {"Content-Type": "application/json", "User-Agent": "Terminal_Lily/0.1"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = json.dumps(payload).encode("utf-8")
        return urllib.request.Request(self.url, data=body, headers=headers, method="POST")

    def chat(self, payload):
        try:
            with urllib.request.urlopen(self._request(payload), timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return Reply(data, resp.headers.get("X-Routed-Via", ""))
        except urllib.error.HTTPError as err:   # must come before URLError
            detail = err.read().decode("utf-8", "replace")[:200]
            raise LLMError(f"router answered HTTP {err.code}: {detail}") from err
        except (urllib.error.URLError, OSError) as err:
            raise LLMError(f"cannot reach the router at {self.url}: {err}") from err
        except ValueError as err:
            raise LLMError("the router sent a reply that is not valid JSON") from err
