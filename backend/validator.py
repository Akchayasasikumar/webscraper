"""
validator.py — Confirm a candidate {container_selector, field_selector} pair
               satisfies the interpreted query on the given HTML.
"""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

_PRICE_RE  = re.compile(
    r"[\u20b9$\u00a3\u20ac\u00a5\u20a9][\d,\.\s]+"
    r"|\d[\d,\.]+\s*(USD|EUR|INR|GBP|Rs)"
    r"|Rs\.?\s*[\d,\.]+"
    r"|INR\s*[\d,\.]+",
    re.I
)
_RATING_RE = re.compile(r"^\d(\.\d+)?$")


def _type_ok(text: str, field: str) -> bool:
    if field == "price":
        return bool(_PRICE_RE.search(text))
    if field == "rating":
        return bool(_RATING_RE.match(text.strip()))
    return bool(text.strip())


def validate(
    html: str,
    candidate: dict[str, str],
    interpreted: dict[str, Any],
) -> dict:
    """
    Validate a candidate pair against the HTML.

    Returns:
        {
          "valid":   bool,
          "reason":  str,
          "items":   list[str]  — matched & typed values (preview, max 5),
          "count":   int,
        }
    """
    container_sel = candidate.get("container_selector", "")
    field_sel     = candidate.get("field_selector", "")
    field         = interpreted.get("field", "name")
    filter_kw     = interpreted.get("filter_keyword")
    multiple      = interpreted.get("multiple", True)

    if not container_sel or not field_sel:
        return {"valid": False, "reason": "Empty selector pair", "items": [], "count": 0}

    try:
        soup = BeautifulSoup(html, "lxml")
        containers = soup.select(container_sel)
    except Exception as exc:
        return {"valid": False, "reason": f"Selector error: {exc}", "items": [], "count": 0}

    if not containers:
        return {
            "valid": False,
            "reason": f"Container '{container_sel}' matched 0 elements",
            "items": [], "count": 0,
        }

    matched_values: list[str] = []
    for c in containers:
        full_text = c.get_text(" ", strip=True).lower()
        if filter_kw and filter_kw.lower() not in full_text:
            continue
        field_el = c.select_one(field_sel)
        if not field_el:
            continue
        text = field_el.get_text(strip=True)
        if text and _type_ok(text, field):
            matched_values.append(text)

    if not matched_values:
        return {
            "valid": False,
            "reason": (
                f"Field '{field_sel}' inside '{container_sel}' "
                f"yielded no values matching type '{field}'"
                + (f" for filter '{filter_kw}'" if filter_kw else "")
            ),
            "items": [], "count": 0,
        }

    # For single-item queries, at least one is enough
    if not multiple and len(matched_values) < 1:
        return {
            "valid": False,
            "reason": "Expected at least 1 item, found 0",
            "items": [], "count": 0,
        }

    return {
        "valid": True,
        "reason": "OK",
        "items": matched_values[:5],
        "count": len(matched_values),
    }
