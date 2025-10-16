from __future__ import annotations

import os
import re
from html import unescape
from typing import Dict, List
from urllib.parse import urlparse

import httpx


def build_feed_url(tpl: str) -> str:
    tpl = (tpl or "").strip()
    if tpl.startswith("rsshub://"):
        host = os.environ.get("RSSHUB_HOST", "rsshub")
        port = int(os.environ.get("RSSHUB_PORT", "1200"))
        path = tpl[len("rsshub://"):].lstrip("/")
        return f"http://{host}:{port}/{path}"
    # Accept http(s) URLs directly
    parsed = urlparse(tpl)
    if parsed.scheme in {"http", "https"}:
        return tpl
    return tpl

_SCRIPT_TAG_RE = re.compile(r"(?is)<(script|style)[^>]*>.*?</\\1>")

_TAG_RE = re.compile(r"<[^>]+>")

_WHITESPACE_RE = re.compile(r"\s+")

def _strip_html(value: str | None) -> str:
    if value is None:
        return ""
    text = unescape(str(value))
    if not text:
        return ""
    text = _SCRIPT_TAG_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text

def _sanitize_field(value: str | None) -> str | None:
    cleaned = _strip_html(value)
    return cleaned if cleaned else None

def fetch_items(url: str) -> List[Dict]:
    """Fetch feed items from URL with robust RSS/Atom parsing.

    Behavior:
    - If the endpoint returns a JSON list of items (RSSHub normalized), map fields directly.
    - Otherwise, parse as XML using `feedparser` to support RSS (incl. namespaces/CDATAs) and Atom.
    - For XML, populate `url`, `title`, `summary`, `published_at`; leave `content=None` so the
      downstream backfill step can fetch full article content consistently.
    """
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=None, pool=None)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()

        # 1) Prefer normalized JSON list if provided by source
        try:
            data = r.json()
            if isinstance(data, list):
                cleaned_items: List[Dict] = []
                for it in data:
                    if not isinstance(it, dict):
                        continue
                    summary = _sanitize_field(it.get("summary"))
                    content = _sanitize_field(it.get("content"))
                    cleaned_items.append(
                        {
                            "url": str(it.get("url") or it.get("link") or "").strip(),
                            "title": it.get("title"),
                            "summary": summary,
                            "content": content,
                            "published_at": it.get("published_at") or it.get("pubDate") or it.get("updated"),
                        }
                    )
                return cleaned_items
        except Exception:
            pass

        # 2) Robust XML parse (RSS/Atom)
        try:
            import feedparser  # type: ignore
        except Exception as e:  # pragma: no cover
            # As a last resort, return empty to avoid breaking the pipeline
            return []

        parsed = feedparser.parse(r.text)
        out: List[Dict] = []
        for e in getattr(parsed, "entries", []) or []:
            link = getattr(e, "link", None) or getattr(e, "id", None)
            if not link:
                # Try links collection if present
                links = getattr(e, "links", []) or []
                for li in links:
                    href = None
                    try:
                        href = li.get("href") if isinstance(li, dict) else getattr(li, "href", None)
                    except Exception:
                        href = None
                    if href:
                        link = href
                        break
            title = getattr(e, "title", None)
            # For consistency, prefer cleaned summary for preview only
            summary = _sanitize_field(getattr(e, "summary", None) or getattr(e, "description", None))
            # Try to extract fulltext content from common fields: Atom <content>, RSS <content:encoded>
            content_val = None
            try:
                cont_list = getattr(e, "content", None)
                if isinstance(cont_list, list) and cont_list:
                    for c in cont_list:
                        try:
                            v = c.get("value") if isinstance(c, dict) else getattr(c, "value", None)
                        except Exception:
                            v = None
                        if v and str(v).strip():
                            cleaned_val = _sanitize_field(str(v))
                            if cleaned_val:
                                content_val = cleaned_val
                                break
                            break
                # Some feeds may expose raw key 'content:encoded'
                if not content_val and isinstance(e, dict):
                    raw = e.get("content:encoded")
                    if raw and str(raw).strip():
                        cleaned_raw = _sanitize_field(str(raw))
                        if cleaned_raw:
                            content_val = cleaned_raw
            except Exception:
                content_val = None
            published = (
                getattr(e, "published", None)
                or getattr(e, "updated", None)
                or getattr(e, "issued", None)
            )
            out.append(
                {
                    "url": str(link or "").strip(),
                    "title": title,
                    "summary": summary,
                    "content": content_val,
                    "published_at": published,
                }
            )
        return out
