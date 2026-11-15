"""A tiny fake MCP server (Streamable HTTP) on localhost, for tests."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
ECHO = {"name": "echo", "description": "Echo text", "inputSchema": SCHEMA}
BOOM = {"name": "boom", "description": "Always fails"}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        server = self.server
        size = int(self.headers.get("Content-Length", 0))
        message = json.loads(self.rfile.read(size))
        server.log.append({
            "method": message.get("method"),
            "auth": self.headers.get("Authorization"),
            "session": self.headers.get("Mcp-Session-Id"),
        })
        if server.token and self.headers.get("Authorization") != f"Bearer {server.token}":
            return self._send(401, b"unauthorized")
        if "id" not in message:
            return self._send(202, b"")
        self._reply(message)

    def _reply(self, message):
        method, params = message["method"], message.get("params", {})
        body = {"jsonrpc": "2.0", "id": message["id"]}
        if method == "initialize":
            body["result"] = {"protocolVersion": "2025-06-18", "capabilities": {}}
        elif method == "tools/list" and not params.get("cursor"):
            body["result"] = {"tools": [ECHO], "nextCursor": "page2"}
        elif method == "tools/list":
            body["result"] = {"tools": [BOOM]}
        elif method == "tools/call" and params["name"] == "echo":
            text = params["arguments"]["text"]
            body["result"] = {"content": [{"type": "text", "text": text.upper()}]}
        elif method == "tools/call":
            body["result"] = {"content": [{"type": "text", "text": "kaput"}], "isError": True}
        else:
            body["error"] = {"code": -32601, "message": "method not found"}
        payload = json.dumps(body).encode()
        if self.server.sse:
            note = b'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/message"}\n\n'
            payload = note + b"event: message\ndata: " + payload + b"\n\n"
        kind = "text/event-stream" if self.server.sse else "application/json"
        self._send(200, payload, kind, session="sess1" if method == "initialize" else None)

    def _send(self, status, body, kind="text/plain", session=None):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        if session:
            self.send_header("Mcp-Session-Id", session)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start_server(case, token="", sse=False):
    """Start the fake server for one test case; it is cleaned up automatically."""
    env = mock.patch.dict(os.environ, {"no_proxy": "127.0.0.1", "NO_PROXY": "127.0.0.1"})
    env.start()
    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.token, server.sse, server.log = token, sse, []
    server.url = f"http://127.0.0.1:{server.server_port}/mcp"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    case.addCleanup(env.stop)
    case.addCleanup(server.server_close)
    case.addCleanup(server.shutdown)
    return server
