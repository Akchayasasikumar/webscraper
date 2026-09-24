"""
pipeline.py — Orchestrates the full self-healing loop per query.

DETECT → UNDERSTAND → OPTIMIZE → VALIDATE → REPAIR → RESUME

run_query(url, query, html, state) -> dict  (structured result)

This single function handles both single-query and batch use cases.
The state dict is updated in-place for live /scraper/status polling.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from candidate_generator import generate_candidates
from database import get_selectors, insert_history, save_selectors
from failure_detector import is_failure
from quantum_optimizer import rank_candidates
from query_interpreter import interpret
from scraper import extract, extract_filtered
from validator import validate

logger = logging.getLogger(__name__)

STEPS = [
    "LOADING_PAGE",
    "CONNECTED",
    "SCRAPING",
    "FAILURE_DETECTED",
    "ANALYZING",
    "GENERATING_CANDIDATES",
    "OPTIMIZING",
    "VALIDATING",
    "REPAIRED",
    "RESUMED",
]


def _set(state: dict, step: str, extra: dict | None = None) -> None:
    state["pipeline_step"] = step
    state["pipeline_steps_done"] = STEPS[: STEPS.index(step) + 1] if step in STEPS else []
    if extra:
        state.update(extra)
    logger.info("Step: %s", step)


def run_query(
    url: str,
    query: str,
    html: str,
    state: dict,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Run the full DETECT→RESUME pipeline for one query.

    Returns a structured result dict:
    {
        "query":        str,
        "interpreted":  dict,
        "items":        list[str],     # extracted field values
        "old_selectors": dict,
        "new_selectors": dict | None,
        "candidates":   list[dict],
        "ranked":       list[dict],
        "validation":   list[dict],
        "method":       str,           # "quantum" | "classical_fallback"
        "final_status": str,           # "ok" | "healed" | "failed" | ...
        "failure_reason": str,
        "candidate_source": str,
    }
    """
    result: dict[str, Any] = {
        "query":          query,
        "interpreted":    {},
        "items":          [],
        "old_selectors":  {},
        "new_selectors":  None,
        "candidates":     [],
        "ranked":         [],
        "validation":     [],
        "method":         "classical_fallback",
        "final_status":   "failed",
        "failure_reason": "",
        "candidate_source": "heuristic",
    }

    # ── UNDERSTAND ────────────────────────────────────────────────────────────
    state["status"] = "scraping"
    _set(state, "CONNECTED")
    interpreted = interpret(query)
    result["interpreted"] = interpreted
    state["current_query"] = query
    state["interpreted"]   = interpreted
    time.sleep(0.2)

    # ── DETECT ────────────────────────────────────────────────────────────────
    _set(state, "SCRAPING")

    old_selectors = get_selectors(url, query) or {}
    result["old_selectors"] = old_selectors

    cs = old_selectors.get("container_selector")
    fs = old_selectors.get("field_selector")

    if cs and fs:
        items_raw = extract(html, cs, fs, interpreted.get("filter_keyword"))
    else:
        items_raw = []

    failed, reason = is_failure(items_raw, interpreted, cs, fs)

    if not failed:
        # Happy path — selector works fine
        items = [r["text"] for r in items_raw if r.get("matched") and r.get("text")]
        result["items"]        = items
        result["final_status"] = "ok"
        _set(state, "RESUMED", {
            "status":     "scraping",
            "last_items": items[:5],
        })
        insert_history(
            url=url, query=query, interpreted=interpreted,
            old_selectors=old_selectors, new_selectors=None,
            candidates=[], scores=[], method="none",
            validation_ok=True, final_status="ok",
            result_items=items,
            user_id=user_id,
        )
        return result

    # ── FAILURE DETECTED ──────────────────────────────────────────────────────
    logger.warning("Extraction failed: %s", reason)
    result["failure_reason"] = reason
    _set(state, "FAILURE_DETECTED")
    state["status"] = "healing"
    time.sleep(0.3)

    # ── ANALYZE DOM ───────────────────────────────────────────────────────────
    _set(state, "ANALYZING")
    time.sleep(0.4)

    # ── GENERATE CANDIDATES ───────────────────────────────────────────────────
    _set(state, "GENERATING_CANDIDATES")
    gen = generate_candidates(html, interpreted, old_selectors)
    candidates   = gen["candidates"]
    cand_source  = gen["source"]
    result["candidates"]      = candidates
    result["candidate_source"] = cand_source
    logger.info("Generated %d candidates via %s", len(candidates), cand_source)
    time.sleep(0.3)

    if not candidates:
        result["failure_reason"] = "No candidates generated"
        insert_history(
            url=url, query=query, interpreted=interpreted,
            old_selectors=old_selectors, new_selectors=None,
            candidates=[], scores=[], method="none",
            validation_ok=False, final_status="no_candidates",
            failure_reason=result["failure_reason"],
            user_id=user_id,
        )
        state["status"] = "failed"
        return result

    # ── OPTIMIZE ──────────────────────────────────────────────────────────────
    _set(state, "OPTIMIZING")
    opt    = rank_candidates(candidates, html, interpreted, old_selectors)
    ranked = opt["ranked"]
    method = opt["method"]
    result["ranked"] = ranked
    result["method"] = method
    logger.info("Ranked %d candidates via %s", len(ranked), method)
    time.sleep(0.4)

    # ── VALIDATE ──────────────────────────────────────────────────────────────
    _set(state, "VALIDATING")
    validation_log: list[dict] = []
    chosen_candidate: dict | None = None
    chosen_items: list[str] = []

    for entry in ranked:
        cand = entry["candidate"]
        v    = validate(html, cand, interpreted)
        validation_log.append({
            "candidate": cand,
            "score":     entry["score"],
            "valid":     v["valid"],
            "reason":    v["reason"],
            "items":     v["items"],
        })
        logger.info("Validate %s: %s", cand, v["reason"])
        if v["valid"]:
            chosen_candidate = cand
            chosen_items     = v["items"]
            break

    result["validation"] = validation_log
    time.sleep(0.3)

    # ── REPAIR / RESUME ───────────────────────────────────────────────────────
    if chosen_candidate:
        # Get full item list (not just preview)
        full_items = extract_filtered(
            html,
            chosen_candidate["container_selector"],
            chosen_candidate["field_selector"],
            interpreted.get("filter_keyword"),
        )
        result["items"]        = full_items
        result["new_selectors"] = chosen_candidate
        result["final_status"] = "healed"

        save_selectors(
            url, query,
            chosen_candidate["container_selector"],
            chosen_candidate["field_selector"],
        )

        insert_history(
            url=url, query=query, interpreted=interpreted,
            old_selectors=old_selectors, new_selectors=chosen_candidate,
            candidates=candidates, scores=ranked, method=method,
            validation_ok=True, final_status="healed",
            result_items=full_items,
            user_id=user_id,
        )

        _set(state, "REPAIRED", {
            "new_selectors": chosen_candidate,
            "last_items":    full_items[:5],
        })
        time.sleep(0.4)
        _set(state, "RESUMED")
        state["status"]    = "scraping"
        state["last_items"] = full_items[:5]

    else:
        result["failure_reason"] = "No candidate passed validation"
        insert_history(
            url=url, query=query, interpreted=interpreted,
            old_selectors=old_selectors, new_selectors=None,
            candidates=candidates, scores=ranked, method=method,
            validation_ok=False, final_status="validation_failed",
            failure_reason=result["failure_reason"],
            user_id=user_id,
        )
        state["status"] = "failed"
        logger.error("Healing failed: no valid selector found.")

    return result
