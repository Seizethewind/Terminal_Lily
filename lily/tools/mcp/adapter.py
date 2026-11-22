"""Turns the tools of an MCP server into normal Lily tools."""
import re

from lily.tools.base import BaseTool
from lily.tools.mcp.client import McpClient
from lily.tools.mcp.config import load_servers, token_is_safe
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("mcp")
CONNECT_TIMEOUT = 8   # seconds, so a dead server cannot stall startup for long
CALL_TIMEOUT = 60


def _safe(text):
    return re.sub(r"[^A-Za-z0-9_-]", "_", text)


class McpTool(BaseTool):
    def __init__(self, lily, client, server, spec):
        super().__init__(lily)
        self.client = client
        self.remote_name = spec["name"]
        self.name = f"{_safe(server)}__{_safe(spec['name'])}"[:64]
        self.description = spec.get("description") or f"{spec['name']} (from {server})"
        self.parameters = spec.get("inputSchema") or {"type": "object", "properties": {}}

    def run(self, **args):
        return self.client.call_tool(self.remote_name, args)


def load(lily, servers=None, client_factory=McpClient):
    """Connect to every enabled MCP server. Returns (tools, errors)."""
    try:
        servers = load_servers() if servers is None else servers
    except LilyError as err:
        return [], [str(err)]
    tools, errors = [], []
    for server in servers:
        try:
            if server["auth_env"] and not server["token"]:
                raise LilyError(f"{server['auth_env']} is not set (put it in .env)")
            if server["token"] and not token_is_safe(server["url"]):
                raise LilyError("it sends a token, so its url must start with https://")
            client = client_factory(server["url"], server["token"], CONNECT_TIMEOUT)
            client.connect()
            specs = client.list_tools()
            client.timeout = CALL_TIMEOUT
            tools += [McpTool(lily, client, server["name"], spec) for spec in specs]
        except LilyError as err:
            log.warning("mcp %s: %s", server["name"], err)
            errors.append(f"mcp {server['name']}: {err}")
    return tools, errors
