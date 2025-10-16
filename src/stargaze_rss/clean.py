from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

_CONTROL_CHARS = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")
_WHITESPACE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    try:
        import bleach  # type: ignore

        # Remove scripts/styles entirely; keep only text content
        # Pre-strip script/style blocks to drop their content
        text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
        text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
        return bleach.clean(
            text,
            tags=[],
            attributes={},
            strip=True,
        )
    except Exception:
        # Fallback: strip script/style then remove remaining tags
        text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
        text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
        return re.sub(r"<[^>]+>", " ", text)


def _normalize_quotes(text: str) -> str:
    # Map common typographic quotes to ASCII equivalents
    return (
        text.replace("“", '"').replace("”", '"').replace("„", '"').replace("‟", '"')
        .replace("’", "'").replace("‘", "'").replace("‚", "'").replace("‛", "'")
    )


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _remove_control_chars(text: str) -> str:
    return _CONTROL_CHARS.sub("", text)


def _maybe_truncate(text: str) -> str:
    try:
        max_len = int(os.environ.get("NLP_MAX_TEXT_LEN", "0"))
    except Exception:
        max_len = 0
    if max_len and max_len > 0 and len(text) > max_len:
        return text[:max_len]
    return text


def detect_language(text: str) -> Optional[str]:  # pragma: no cover - best effort
    try:
        from langdetect import detect  # type: ignore

        return detect(text)
    except Exception:
        return None


@dataclass(frozen=True)
class CleanResult:
    text: str
    lang: Optional[str]


def clean_text(raw: str, *, with_lang: bool = True) -> CleanResult:
    """Lightweight, deterministic text sanitizer for RSS ingest.

    - strips HTML and scripts
    - removes control chars
    - normalizes quotes
    - collapses whitespace
    - optionally truncates to NLP_MAX_TEXT_LEN
    - best-effort language detection (optional)
    """
    if not isinstance(raw, str):
        raw = str(raw or "")
    t = _strip_html(raw)
    t = _remove_control_chars(t)
    t = _normalize_quotes(t)
    t = _collapse_whitespace(t)
    t = _maybe_truncate(t)
    lang = detect_language(t) if with_lang else None
    return CleanResult(text=t, lang=lang)

