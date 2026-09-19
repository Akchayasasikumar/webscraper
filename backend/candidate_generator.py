"""
candidate_generator.py — Generate {container_selector, field_selector} candidate pairs.

Default engine: heuristic DOM analysis (always works, no API key).
Optional engine: Claude API (guarded by ANTHROPIC_API_KEY env var).

Public API:
    generate_candidates(html, interpreted, old_selectors)
        -> {"candidates": list[{container_selector, field_selector}], "source": "heuristic"|"llm"}
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

_PRICE_RE  = re.compile(
    r"[\u20b9$\u00a3\u20ac\u00a5\u20a9][\d,\.\s]+"
    r"|\d[\d,\.]+\s*(USD|EUR|INR|GBP|Rs)"
    r"|Rs\.?\s*[\d,\.]+"
    r"|INR\s*[\d,\.]+",
    re.I
)
_RATING_RE = re.compile(r"^\d(\.\d+)?$")

# Field-specific class/id hint words
_FIELD_HINTS: dict[str, list[str]] = {
    "price":  ["price", "cost", "amount", "fee", "mrp", "rate", "pricing", "charge"],
    "rating": ["rating", "star", "stars", "score", "review", "grade"],
    "name":   ["name", "title", "heading", "product", "label", "item"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _text_matches_field(text: str, field: str) -> bool:
    if field == "price":
        return bool(_PRICE_RE.search(text))
    if field == "rating":
        return bool(_RATING_RE.match(text.strip()))
    return bool(text.strip())


def _class_hints_match(el: Tag, field: str) -> int:
    """Return how many class/id tokens match the field's hint words."""
    classes = " ".join(el.get("class", []))
    el_id   = el.get("id", "")
    combo   = (classes + " " + el_id).lower()
    return sum(1 for h in _FIELD_HINTS.get(field, []) if h in combo)


def _selector_for(el: Tag) -> str:
    """Build a short, reliable CSS selector for an element.

    Picks the single most descriptive class to avoid broken multi-class
    BEM selectors like `span.price-item--regular.price-item` that may
    not parse cleanly in all BeautifulSoup CSS contexts.
    """
    classes = el.get("class", [])
    el_id   = el.get("id", "")
    tag     = el.name or "div"
    if el_id:
        return f"#{el_id}"
    if classes:
        # Prefer the longest class name — usually the most specific BEM modifier
        best_cls = max(classes, key=len)
        # Escape any characters that break CSS selectors (shouldn't be needed
        # for valid HTML class names, but be safe)
        safe_cls = best_cls.replace(":", "\\:")
        return f"{tag}.{safe_cls}"
    return tag


def _is_repeating_container(soup: BeautifulSoup, selector: str, min_count: int = 2) -> bool:
    """True if the selector matches at least min_count elements — looks like a list."""
    try:
        return len(soup.select(selector)) >= min_count
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic engine
# ─────────────────────────────────────────────────────────────────────────────

def _heuristic_candidates(
    html: str,
    interpreted: dict[str, Any],
    old_selectors: dict[str, str],
) -> list[dict[str, str]]:
    """
    Strategy:
    1. Find LEAF elements that contain the expected field pattern (price/rating/name).
       Leaf = element whose direct text matches the field, with few or no child tags.
    2. For each such element, walk up to a likely repeating container parent.
    3. Build (container_selector, field_selector) pairs.
    4. De-duplicate and rank by evidence strength.
    """
    field          = interpreted.get("field", "name")
    old_container  = old_selectors.get("container_selector", "")
    old_field      = old_selectors.get("field_selector", "")

    soup = BeautifulSoup(html, "lxml")
    scored: list[tuple[float, dict[str, str]]] = []

    # Walk every element looking for field matches
    for el in soup.find_all(True):
        if el.name in ("html", "head", "body", "script", "style", "meta", "link", "nav", "header", "footer"):
            continue

        # Prefer elements whose OWN text (not children's text) matches the field
        # This avoids grabbing the whole product card
        own_text = el.get_text(strip=True)
        if not own_text:
            continue

        # Count child tags — a real field element should have few/no child tags
        child_tags = [c for c in el.children if hasattr(c, "name") and c.name]
        child_tag_count = len(child_tags)

        # Skip elements with too many children — they're containers, not field elements
        if child_tag_count > 4:
            continue

        # Score as a field element
        field_score = 0.0
        if _text_matches_field(own_text, field):
            field_score += 3.0
            # Bonus for being a true leaf (no child tags at all)
            if child_tag_count == 0:
                field_score += 2.0
        hint_matches = _class_hints_match(el, field)
        field_score += hint_matches * 2.0
        if field_score < 1.0:
            continue

        # Old selector similarity bonus
        el_sel = _selector_for(el)
        old_tokens = set(re.findall(r"[\w-]+", old_field))
        new_tokens = set(re.findall(r"[\w-]+", el_sel))
        field_score += len(old_tokens & new_tokens) * 1.5

        # Skip overly generic selectors with no class or id (e.g. bare "div", "li", "span")
        if el_sel in ("div", "li", "span", "p", "a", "td", "tr"):
            field_score -= 2.0
        if field_score < 1.0:
            continue

        field_selector = el_sel

        # Walk up to find a plausible repeating container
        parent = el.parent
        for _ in range(6):  # look up to 6 levels
            if parent is None or parent.name in ("[document]", "body", "html"):
                break
            container_sel = _selector_for(parent)

            # Skip overly generic containers (bare tag, no class/id)
            if container_sel in ("div", "li", "ul", "ol", "section", "article", "main"):
                parent = parent.parent
                continue

            if _is_repeating_container(soup, container_sel, min_count=2):
                # Container similarity to old
                old_c_tokens = set(re.findall(r"[\w-]+", old_container))
                new_c_tokens = set(re.findall(r"[\w-]+", container_sel))
                container_score = field_score + len(old_c_tokens & new_c_tokens) * 1.5

                # Verify field_selector works inside the container
                try:
                    containers = soup.select(container_sel)
                    working = sum(
                        1 for c in containers[:8]
                        if c.select_one(field_selector) and
                        _text_matches_field(c.select_one(field_selector).get_text(strip=True), field)
                    )
                    if working > 0:
                        container_score += working * 1.0
                    else:
                        parent = parent.parent
                        continue
                except Exception:
                    pass

                scored.append((container_score, {
                    "container_selector": container_sel,
                    "field_selector":     field_selector,
                }))
                break
            parent = parent.parent

    # De-duplicate, keep highest score per (container, field) pair
    seen: dict[tuple, float] = {}
    for score, pair in scored:
        key = (pair["container_selector"], pair["field_selector"])
        if key not in seen or seen[key] < score:
            seen[key] = score

    ranked = sorted(seen.items(), key=lambda x: x[1], reverse=True)
    return [dict(zip(["container_selector", "field_selector"], k)) for k, _ in ranked[:5]]



# ─────────────────────────────────────────────────────────────────────────────
# Optional LLM engine
# ─────────────────────────────────────────────────────────────────────────────

def _llm_candidates(
    html: str,
    interpreted: dict[str, Any],
    old_selectors: dict[str, str],
) -> list[dict[str, str]]:
    import anthropic  # type: ignore

    html_snippet = html[:4000] if len(html) > 4000 else html
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = (
        f"You are a CSS selector expert. A web scraper has failed to extract '{interpreted['field']}' values.\n"
        f"Old container selector: '{old_selectors.get('container_selector', 'none')}'\n"
        f"Old field selector: '{old_selectors.get('field_selector', 'none')}'\n\n"
        f"HTML:\n```html\n{html_snippet}\n```\n\n"
        f"Return ONLY a JSON array of 3-5 objects, each with 'container_selector' and 'field_selector' keys, "
        f"ordered most-likely first. The container_selector should match the repeating product card element; "
        f"the field_selector (relative) should match the {interpreted['field']} element inside it.\n"
        f"Raw JSON only, no markdown."
    )
    message = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("```").strip()
    candidates = json.loads(raw)
    assert isinstance(candidates, list)
    return [
        {"container_selector": str(c["container_selector"]),
         "field_selector":     str(c["field_selector"])}
        for c in candidates if "container_selector" in c and "field_selector" in c
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_candidates(
    html: str,
    interpreted: dict[str, Any],
    old_selectors: dict[str, str],
) -> dict[str, Any]:
    """
    Returns:
        {
          "candidates": [{"container_selector": str, "field_selector": str}, ...],
          "source":     "heuristic" | "llm"
        }
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            candidates = _llm_candidates(html, interpreted, old_selectors)
            if candidates:
                logger.info("Candidate generation via LLM: %d pairs", len(candidates))
                return {"candidates": candidates, "source": "llm"}
        except Exception as exc:
            logger.warning("LLM candidate generation failed (%s); falling back to heuristic.", exc)

    candidates = _heuristic_candidates(html, interpreted, old_selectors)
    logger.info("Candidate generation via heuristic: %d pairs", len(candidates))
    return {"candidates": candidates, "source": "heuristic"}
