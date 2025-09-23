from __future__ import annotations

import re

from html import unescape


def extract_content(html: str) -> str:
    # Prefer <article> blocks
    m = re.search(r"<article[^>]*>([\s\S]*?)</article>", html, re.IGNORECASE)
    if m:
        html = m.group(1)
    # Strip scripts/styles
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
