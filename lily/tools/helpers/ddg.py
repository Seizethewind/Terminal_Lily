"""DuckDuckGo HTML search. Unofficial: it may break if the page layout changes."""
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from lily.utils.errors import ToolError

URL = "https://html.duckduckgo.com/html/"
AGENT = "Mozilla/5.0 (Android; Mobile) Terminal_Lily/0.1"
MAX_BYTES = 1_000_000   # a results page is far smaller; this stops a huge reply from filling the phone's memory


def _real_url(href):
    """DuckDuckGo wraps links in a redirect; pull the real address out."""
    if href.startswith("//"):
        href = "https:" + href
    target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg")
    return target[0] if target else href


class _Results(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._kind = None
        self._href = ""
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if "result__a" in classes:
            self._kind, self._href, self._text = "title", attrs.get("href") or "", []
        elif "result__snippet" in classes:
            self._kind, self._text = "snippet", []

    def handle_data(self, data):
        if self._kind:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self._kind:
            return
        text = " ".join("".join(self._text).split())
        if self._kind == "title":
            self.results.append({"title": text, "url": _real_url(self._href), "snippet": ""})
        elif self.results:
            self.results[-1]["snippet"] = text
        self._kind = None


def parse(html):
    parser = _Results()
    parser.feed(html)
    return parser.results


def search(query, limit=5, url=URL, timeout=15):
    request = urllib.request.Request(
        url + "?" + urllib.parse.urlencode({"q": query}), headers={"User-Agent": AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            html = resp.read(MAX_BYTES).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as err:
        raise ToolError(f"search failed: {err}") from err
    results = parse(html)[:limit]
    if not results:
        raise ToolError("no results (the site may be blocking automated searches)")
    return results
