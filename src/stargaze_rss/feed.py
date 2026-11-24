"""Parse RSS, Atom, or normalized JSON entries."""

from html import unescape
import json
from urllib.parse import urljoin, urlsplit, urlunsplit

import feedparser
import httpx

from .content import extract_content

_MAX_FEED_BYTES = 2 * 1024 * 1024


def _strip_html(value):
    if value is None:
        return ""
    return extract_content(unescape(str(value)))


def canonical_url(value, base=""):
    try:
        url = urlsplit(urljoin(base, str(value or "").strip()))
        if url.scheme not in ("http", "https") or not url.hostname or url.username is not None:
            return ""
        # Validate the port, including malformed or out-of-range values.
        _ = url.port
    except ValueError:
        return ""
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path or "/", url.query, ""))


def _entry(item, base):
    url = canonical_url(item.get("url") or item.get("link") or item.get("id"), base)
    headline = _strip_html(item.get("title"))
    if not url or not headline:
        return None
    content = item.get("content")
    if isinstance(content, list):
        content = next((part.get("value") for part in content if isinstance(part, dict) and part.get("value")), "")
    return {
        "url": url,
        "title": headline,
        "summary": _strip_html(item.get("summary") or item.get("description")),
        "content": _strip_html(content),
        "published_at": item.get("published_at") or item.get("pubDate") or item.get("published") or item.get("updated"),
    }


def parse_feed(contents, *, base_url=""):
    """Return normalized entries from a bytes payload."""
    if len(contents) > _MAX_FEED_BYTES:
        raise ValueError("feed exceeds 2 MiB")
    if contents.lstrip().startswith(b"["):
        items = json.loads(contents)
    else:
        parsed = feedparser.parse(contents)
        if parsed.bozo and not parsed.entries:
            raise ValueError("could not parse RSS or Atom feed")
        items = parsed.entries
    output = []
    for item in items:
        if isinstance(item, dict) and (entry := _entry(item, base_url)):
            output.append(entry)
    return output


def fetch_items(url):
    """Fetch a feed explicitly selected by the caller."""
    url = canonical_url(url)
    if not url:
        raise ValueError("expected an HTTP(S) feed URL without credentials")
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            contents = bytearray()
            for chunk in response.iter_bytes():
                contents.extend(chunk)
                if len(contents) > _MAX_FEED_BYTES:
                    raise ValueError("feed exceeds 2 MiB")
            return parse_feed(bytes(contents), base_url=str(response.url))
