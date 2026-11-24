"""Group duplicate headlines and select representative feed text."""

import re

from .clean import clean_text
from .similarity import _calc_jaccard


def _headline_tokens(title):
    return set(re.findall(r"[^\W_]+", title.casefold()))


def summarize_entries(entries, *, threshold=0.8):
    """Return clusters in source order with a representative extractive summary."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    groups = []
    by_url = set()
    for entry in entries:
        title = entry["title"]
        url = entry["url"]
        if url in by_url:
            continue
        tokens = _headline_tokens(title)
        match = next(
            ((group, existing) for group, existing in groups
             if tokens and existing and _calc_jaccard(tokens, existing) >= threshold),
            None,
        )
        if match is None:
            text = entry.get("summary") or entry.get("content") or title
            cleaned = clean_text(text, with_lang=False).text
            group = {
                "title": title,
                "summary": cleaned[:320].rstrip(),
                "published_at": entry.get("published_at"),
                "sources": [url],
            }
            groups.append((group, tokens))
        else:
            group, _ = match
            group["sources"].append(url)
        by_url.add(url)
    return [group for group, _ in groups]
