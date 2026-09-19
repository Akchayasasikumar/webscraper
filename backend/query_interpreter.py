"""
query_interpreter.py — Translate a free-text query into a structured target.

Result: {field, filter_keyword, multiple, source}

  field          : "price" | "rating" | "name" | "text"
  filter_keyword : str | None  — e.g. "lipstick", None = all items
  multiple       : bool        — whether to extract many items
  source         : "heuristic" | "llm"

Default engine: heuristic keyword parsing (always works, no API key).
Optional engine: Claude API (when ANTHROPIC_API_KEY is set in env).
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Heuristic keyword tables ──────────────────────────────────────────────────

_FIELD_KEYWORDS: dict[str, list[str]] = {
    "price":  ["price", "cost", "amount", "fee", "charge", "pricing", "rate", "mrp"],
    "rating": ["rating", "star", "stars", "score", "review", "grade", "rank"],
    "name":   ["name", "title", "heading", "product", "label", "item"],
}

_MULTIPLE_KEYWORDS = [
    "all", "every", "each", "list", "show", "retrieve", "get",
    "find", "fetch", "extract", "collect", "multiple", "plural",
]

_STOP_WORDS = {
    "retrieve", "get", "find", "fetch", "extract", "show", "list", "collect",
    "all", "every", "each", "the", "a", "an", "of", "on", "in", "at",
    "from", "with", "for", "me", "please", "page", "site", "website",
    "give", "display", "return",
    # Common product category words — should not become filter_keyword
    "jersey", "jerseys", "shirt", "shirts", "kit", "kits", "product", "products",
    "item", "items", "book", "books", "phone", "phones", "laptop", "laptops",
    "shoe", "shoes", "watch", "watches", "bag", "bags",
    # Field plural forms — should not become filter_keyword either
    "prices", "price", "ratings", "rating", "names", "titles",
}


def _heuristic(query: str) -> dict[str, Any]:
    """
    Parse the query string with pure heuristics.
    Returns {field, filter_keyword, multiple}.
    """
    q = query.lower().strip()
    tokens = re.findall(r"[a-zA-Z]+", q)

    # Detect field
    field = "name"  # default
    matched_field_tokens: set[str] = set()
    for f, keywords in _FIELD_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                field = f
                matched_field_tokens.add(kw)
                break
        if matched_field_tokens:
            break

    # Detect multiple
    multiple = any(kw in tokens for kw in _MULTIPLE_KEYWORDS)
    # Also treat plural (ends in 's') hint if a known plural of target words appears
    if not multiple and re.search(r"\bprices\b|\bratings\b|\bnames\b|\btitles\b", q):
        multiple = True

    # Detect filter_keyword — what's left after removing stops + field tokens
    filter_tokens = [
        t for t in tokens
        if t not in _STOP_WORDS
        and t not in matched_field_tokens
        and t not in _FIELD_KEYWORDS.get(field, [])
        and len(t) > 2
    ]
    filter_keyword = filter_tokens[0] if filter_tokens else None

    return {"field": field, "filter_keyword": filter_keyword, "multiple": multiple}


def _llm_interpret(query: str) -> dict[str, Any]:
    """
    Call Claude API to interpret the query.
    Raises on any failure — caller will fall back to heuristic.
    """
    import anthropic  # type: ignore — optional dependency

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = (
        "You are a web-scraping assistant. Given a natural-language query about what to extract "
        "from a web page, return ONLY a JSON object with exactly three keys:\n"
        '  "field": one of "price" | "rating" | "name"\n'
        '  "filter_keyword": a noun that filters which items to include (e.g. "lipstick"), '
        "or null if all items should be included\n"
        '  "multiple": true if multiple items are expected, false for a single item\n\n'
        f'Query: "{query}"\n\n'
        "Return raw JSON only, no markdown fences, no explanation."
    )
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("```").strip()
    parsed = json.loads(raw)
    # Validate structure
    assert "field" in parsed and "multiple" in parsed
    assert parsed["field"] in ("price", "rating", "name", "text")
    return {
        "field":          str(parsed["field"]),
        "filter_keyword": parsed.get("filter_keyword") or None,
        "multiple":       bool(parsed["multiple"]),
    }


def interpret(query: str) -> dict[str, Any]:
    """
    Interpret a free-text query into a structured target descriptor.

    Returns:
        {
            "field":          str,        # "price" | "rating" | "name"
            "filter_keyword": str | None, # e.g. "lipstick", or None
            "multiple":       bool,
            "source":         "heuristic" | "llm",
        }
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            result = _llm_interpret(query)
            result["source"] = "llm"
            logger.info("Query interpreted via LLM: %s", result)
            return result
        except Exception as exc:
            logger.warning("LLM interpretation failed (%s); falling back to heuristic.", exc)

    result = _heuristic(query)
    result["source"] = "heuristic"
    logger.info("Query interpreted via heuristic: %s", result)
    return result
