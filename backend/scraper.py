"""
scraper.py — List-aware extraction using container + field selectors.

Container selector: selects each repeating product "card" element.
Field selector:     relative to the container, selects the specific field (price, name, rating).

Main functions:
  extract(html, container_selector, field_selector, filter_keyword=None)
      -> list[{"text": str, "matched": bool}]
  fetch_html(url) -> str
  scrape(url, container_selector, field_selector, filter_keyword=None) -> dict
"""
from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup, Tag


def fetch_html(url: str, timeout: int = 10) -> str:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "SelfHealingScraper/2.0"})
    resp.raise_for_status()
    return resp.text


def extract(
    html: str,
    container_selector: str,
    field_selector: str,
    filter_keyword: str | None = None,
) -> list[dict]:
    """
    Extract field values from all matching containers.

    Returns a list of dicts:
        {"text": str, "matched": bool}

    If filter_keyword is given, 'matched' is True only for containers
    whose full text contains the keyword (case-insensitive).
    If filter_keyword is None, all containers have matched=True.
    """
    soup = BeautifulSoup(html, "lxml")
    containers = soup.select(container_selector)
    results = []

    for container in containers:
        # Get the text of the whole container for filter matching
        full_text = container.get_text(" ", strip=True).lower()
        if filter_keyword:
            matched = filter_keyword.lower() in full_text
        else:
            matched = True

        # Extract field value
        field_el = container.select_one(field_selector)
        if field_el:
            text = field_el.get_text(strip=True)
        else:
            text = ""

        results.append({"text": text, "matched": matched})

    return results


def extract_filtered(
    html: str,
    container_selector: str,
    field_selector: str,
    filter_keyword: str | None = None,
) -> list[str]:
    """
    Like extract(), but returns only the 'text' of matched items.
    Convenience helper used by the pipeline for final result assembly.
    """
    raw = extract(html, container_selector, field_selector, filter_keyword)
    return [r["text"] for r in raw if r["matched"] and r["text"]]


def scrape(
    url: str,
    container_selector: str,
    field_selector: str,
    filter_keyword: str | None = None,
    timeout: int = 10,
) -> dict:
    """
    Full scrape: fetch + extract.
    Returns {"items": list[str], "html": str, "error": str|None, "all_items": list[dict]}
    """
    try:
        html = fetch_html(url, timeout=timeout)
        all_items = extract(html, container_selector, field_selector, filter_keyword)
        items = [r["text"] for r in all_items if r["matched"] and r["text"]]
        return {"items": items, "html": html, "error": None, "all_items": all_items}
    except Exception as exc:
        return {"items": [], "html": "", "error": str(exc), "all_items": []}
