"""Search the web (DuckDuckGo HTML, no key needed)."""
import os

from lily.tools.base import BaseTool, to_int
from lily.tools.helpers import ddg


class Tool(BaseTool):
    name = "web_search"
    description = "Search the web. Returns the top results with title, link and a short snippet."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "what to search for"},
            "limit": {"type": "integer", "description": "how many results (default 5, max 10)"},
        },
        "required": ["query"],
    }

    def run(self, query, limit=5):
        count = max(1, min(to_int(limit, "limit", 5), 10))
        url = os.environ.get("LILY_SEARCH_URL", ddg.URL)
        lines = []
        for number, item in enumerate(ddg.search(query, count, url=url), start=1):
            lines.append(f"{number}. {item['title']}\n   {item['url']}\n   {item['snippet']}".rstrip())
        return "\n".join(lines)
