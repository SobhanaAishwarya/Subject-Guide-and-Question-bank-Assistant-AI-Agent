"""Text cleaning and helper utilities used by the RAG pipeline."""

from __future__ import annotations

import re
import unicodedata
from typing import List

_WHITESPACE_RE = re.compile(r"[ \t\x0b\x0c\r]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_PAGE_NUMBER_RE = re.compile(r"^\s*(page\s*)?\d{1,4}\s*$", re.IGNORECASE)
_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0e-\x1f\x7f]")
_BR_TAG_RE = re.compile(r"\s*<br\s*/?>\s*", re.IGNORECASE)


def clean_text(raw: str) -> str:
    """
    Normalise raw extracted text.

    Fixes the usual PDF extraction artefacts: ligatures, control characters,
    hyphenated line breaks, isolated page numbers and runaway whitespace.
    """
    if not raw:
        return ""

    text = unicodedata.normalize("NFKC", raw)
    text = _CONTROL_RE.sub(" ", text)
    text = _HYPHEN_BREAK_RE.sub(r"\1\2", text)

    lines: List[str] = []
    for line in text.split("\n"):
        stripped = _WHITESPACE_RE.sub(" ", line).strip()
        if _PAGE_NUMBER_RE.match(stripped):
            continue
        lines.append(stripped)

    text = "\n".join(lines)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def truncate(text: str, limit: int = 160) -> str:
    """Shorten text for display, appending an ellipsis when cut."""
    text = text.strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def human_size(num_bytes: int) -> str:
    """Format a byte count as a human readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def strip_html_breaks(text: str) -> str:
    """
    Replace literal ``<br>`` tags with a plain separator.

    Streamlit's markdown renderer escapes raw HTML by default, so a model
    that packs multi-line table cells with ``<br>`` (a common habit) ends up
    showing the literal tag text instead of a line break.
    """
    return _BR_TAG_RE.sub("; ", text)


def strip_code_fences(text: str) -> str:
    """Remove Markdown code fences so JSON payloads can be parsed."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json|python|text)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()
