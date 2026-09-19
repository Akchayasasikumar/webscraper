"""
failure_detector.py — Decide whether a list-aware extraction result is a failure.

is_failure(items, interpreted) -> (bool, reason: str)

Fails if:
  - No container selector stored (first run / cold start)
  - 0 containers found
  - 0 field values found
  - 0 items matched the filter_keyword (if one was given)
  - Extracted values don't match the expected type pattern for the field
"""
from __future__ import annotations

import re
from typing import Any

_PRICE_RE  = re.compile(r"[₹$£€¥₩][\d,\.\s]+|\d[\d,\.]+\s*(USD|EUR|INR|GBP)", re.I)
_RATING_RE = re.compile(r"^\d(\.\d+)?$")


def _matches_type(text: str, field: str) -> bool:
    if field == "price":
        return bool(_PRICE_RE.search(text))
    if field == "rating":
        return bool(_RATING_RE.match(text))
    # name / text — any non-empty string is fine
    return bool(text.strip())


def is_failure(
    items: list[dict],
    interpreted: dict[str, Any],
    container_selector: str | None = None,
    field_selector: str | None = None,
) -> tuple[bool, str]:
    """
    Args:
        items:               output of scraper.extract() — list of {text, matched}
        interpreted:         output of query_interpreter.interpret()
        container_selector:  may be None on cold start
        field_selector:      may be None on cold start

    Returns:
        (failed: bool, reason: str)
    """
    field = interpreted.get("field", "name")
    filter_keyword = interpreted.get("filter_keyword")

    # Cold start — no selectors stored yet
    if not container_selector or not field_selector:
        return True, "No selectors stored — cold start, healing required"

    # No containers found at all
    if not items:
        return True, "Container selector matched 0 elements"

    # No field values extracted
    if not any(r["text"] for r in items):
        return True, "Field selector matched 0 elements inside containers"

    # No items matching the filter
    if filter_keyword:
        matched = [r for r in items if r["matched"] and r["text"]]
        if not matched:
            return True, f"No items matched filter_keyword='{filter_keyword}'"
        # Type-check matched items
        bad = [r["text"] for r in matched if not _matches_type(r["text"], field)]
        if len(bad) == len(matched):
            return True, f"None of the filtered values match expected type '{field}'"
    else:
        # Type-check all items
        values = [r["text"] for r in items if r["text"]]
        bad = [v for v in values if not _matches_type(v, field)]
        if values and len(bad) == len(values):
            return True, f"Extracted values don't match expected type '{field}'"

    return False, ""


def detect(
    items: list[dict],
    interpreted: dict[str, Any],
    container_selector: str | None = None,
    field_selector: str | None = None,
) -> dict:
    """Convenience wrapper returning a structured detection report."""
    failed, reason = is_failure(items, interpreted, container_selector, field_selector)
    matched_values = [r["text"] for r in items if r.get("matched") and r.get("text")] if items else []
    return {
        "failed": failed,
        "reason": reason,
        "matched_values": matched_values[:5],  # preview
    }
