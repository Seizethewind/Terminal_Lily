"""A small MCP client for the Streamable HTTP transport (JSON-RPC over POST).

It does not support the older "HTTP + SSE" transport.
"""
import json
import threading
import urllib.error
import urllib.request

from lily.utils.errors import ToolError

PROTOCOL = "2025-06-18"


class SessionExpired(ToolError):
    """The server forgot our session (HTTP 404): a new one must be started."""


def _sse_messages(body):
    """Yield the JSON payload of each event in a text/event-stream body."""
    for event in body.replace("\r\n", "\n").split("\n\n"):
        data = "\n".join(line[5:].strip() for line in event.split("\n") if line.startswith("data:"))
        if data:
            yield json.loads(data)


def _find_reply(body, kind, want_id):
    if kind == "text/event-stream":
        messages = list(_sse_messages(body))
    else:
        parsed = json.loads(body)
        messages = parsed if isinstance(parsed, list) else [parsed]
    for message in messages:
        if isinstance(message, dict) and message.get("id") == want_id:
            return message
    raise ToolError("the MCP server sent no reply to the request")


class McpClient:
    def __init__(self, url, token="", timeout=30):
        self.url, self.token, self.timeout = url, token, timeout
        self.session = ""
        self._next_id = 0
        self._lock = threading.RLock()   # workers share one client: one request at a time keeps ids and session straight

    def connect(self):
        info = {"name": "Terminal_Lily", "version": "0.1"}
        with self._lock:
            self._rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": info})
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def list_tools(self):
        tools, cursor = [], None
        while True:
            result = self._rpc("tools/list", {"cursor": cursor} if cursor else {})
            tools += result.get("tools", [])
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, name, args):
        result = self._rpc("tools/call", {"name": name, "arguments": args})
        parts = [p.get("text", "") for p in result.get("content", []) if p.get("type") == "text"]
        text = "\n".join(parts)
        if result.get("isError"):
            raise ToolError(f"{name} failed: {text or 'unknown error'}")
        return text or "(no text output)"

    def _rpc(self, method, params):
        with self._lock:
            try:
                return self._send(method, params)
            except SessionExpired:
                if method == "initialize":
                    raise
                self.connect()   # the server dropped our session: start a new one, then try once more
                return self._send(method, params)

    def _send(self, method, params):
        self._next_id += 1
        message = {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params}
        body, kind = self._post(message)
        try:
            reply = _find_reply(body, kind, self._next_id)
        except ValueError as err:
            raise ToolError("the MCP server sent a reply that is not valid JSON") from err
        if "error" in reply:
            error = reply["error"]
            raise ToolError(f"MCP {method}: {error.get('message', error)}")
        return reply.get("result", {})

    def _post(self, message):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL,
            "User-Agent": "Terminal_Lily/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        data = json.dumps(message).encode("utf-8")
        request = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                self.session = resp.headers.get("Mcp-Session-Id") or self.session
                return resp.read().decode("utf-8"), resp.headers.get_content_type()
        except urllib.error.HTTPError as err:   # must come before URLError
            if err.code == 404 and self.session:
                self.session = ""
                raise SessionExpired("the MCP session expired") from err
            raise ToolError(f"the MCP server answered HTTP {err.code}") from err
        except (urllib.error.URLError, OSError) as err:
            raise ToolError(f"cannot reach the MCP server: {err}") from err
