"""
quantum_optimizer.py — Rank {container_selector, field_selector} candidate pairs
                        using a QAOA circuit on the local Qiskit Aer simulator.

Falls back to classical weighted-sum when Qiskit is not installed.

Public API:
    rank_candidates(candidates, html, interpreted, old_selectors)
        -> {"ranked": list[{candidate, score, features, method}], "method": str}
"""
from __future__ import annotations

import logging
import math
import re
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_PRICE_RE  = re.compile(r"[₹$£€¥₩][\d,\.\s]+|\d[\d,\.]+\s*(USD|EUR|INR|GBP)", re.I)
_RATING_RE = re.compile(r"^\d(\.\d+)?$")


# ── Classical feature extraction ──────────────────────────────────────────────

def _token_similarity(a: str, b: str) -> float:
    """Jaccard similarity of CSS token sets."""
    ta = set(re.findall(r"[\w-]+", a))
    tb = set(re.findall(r"[\w-]+", b))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _specificity(sel: str) -> float:
    ids     = sel.count("#")
    classes = sel.count(".") + sel.count("[") + sel.count(":")
    tags    = len(re.findall(r"\b[a-z][a-z0-9]*\b", sel))
    return min((ids * 3 + classes * 2 + tags) / 12.0, 1.0)


def _container_count_score(html: str, container_selector: str) -> float:
    """Normalised count of containers found (more = more likely a list)."""
    try:
        soup = BeautifulSoup(html, "lxml")
        n = len(soup.select(container_selector))
        return min(n / 8.0, 1.0)
    except Exception:
        return 0.0


def _field_match_score(html: str, container_selector: str, field_selector: str, field: str) -> float:
    """Fraction of containers where the field selector extracts the right type."""
    try:
        soup = BeautifulSoup(html, "lxml")
        containers = soup.select(container_selector)
        if not containers:
            return 0.0
        hits = 0
        for c in containers[:8]:
            el = c.select_one(field_selector)
            if not el:
                continue
            text = el.get_text(strip=True)
            if field == "price" and _PRICE_RE.search(text):
                hits += 1
            elif field == "rating" and _RATING_RE.match(text):
                hits += 1
            elif field in ("name", "text") and text:
                hits += 1
        return hits / len(containers[:8])
    except Exception:
        return 0.0


def _compute_features(
    candidates: list[dict],
    html: str,
    old_selectors: dict[str, str],
    field: str,
) -> list[dict[str, float]]:
    old_c = old_selectors.get("container_selector", "")
    old_f = old_selectors.get("field_selector", "")
    feats = []
    for c in candidates:
        cs = c["container_selector"]
        fs = c["field_selector"]
        feats.append({
            "container_sim":    _token_similarity(cs, old_c),
            "field_sim":        _token_similarity(fs, old_f),
            "container_count":  _container_count_score(html, cs),
            "field_match":      _field_match_score(html, cs, fs, field),
            "specificity":      _specificity(cs) * 0.5 + _specificity(fs) * 0.5,
        })
    return feats


def _classical_score(feat: dict[str, float]) -> float:
    return (
        feat["field_match"]      * 0.45 +
        feat["container_count"]  * 0.25 +
        feat["field_sim"]        * 0.15 +
        feat["container_sim"]    * 0.10 +
        feat["specificity"]      * 0.05
    )


# ── QAOA ranking ──────────────────────────────────────────────────────────────

def _qaoa_rank(
    candidates: list[dict],
    features: list[dict[str, float]],
) -> list[tuple[dict, float]]:
    from qiskit import QuantumCircuit    # type: ignore
    from qiskit.circuit import Parameter # type: ignore
    from qiskit_aer import AerSimulator  # type: ignore

    n = min(len(candidates), 8)
    candidates = candidates[:n]
    features   = features[:n]

    quality = [_classical_score(f) for f in features]

    gamma = Parameter("γ")
    beta  = Parameter("β")

    qc = QuantumCircuit(n)
    for i in range(n):
        qc.h(i)
    for i in range(n):
        qc.rz(2 * gamma * quality[i], i)
    for i in range(n):
        qc.rx(2 * beta, i)
    qc.measure_all()

    bound = qc.assign_parameters({gamma: math.pi / 4, beta: math.pi / 8})
    sim = AerSimulator()
    counts = sim.run(bound, shots=2048).result().get_counts()

    total = sum(counts.values())
    qubit_probs = [0.0] * n
    for bitstring, cnt in counts.items():
        for i, bit in enumerate(reversed(bitstring)):
            if bit == "1":
                qubit_probs[i] += cnt / total

    final = [0.5 * qubit_probs[i] + 0.5 * quality[i] for i in range(n)]
    return sorted(zip(candidates, final), key=lambda x: x[1], reverse=True)


# ── Public API ────────────────────────────────────────────────────────────────

def rank_candidates(
    candidates: list[dict],
    html: str,
    interpreted: dict[str, Any],
    old_selectors: dict[str, str],
) -> dict[str, Any]:
    """
    Returns:
        {
          "ranked": [{"candidate": {container_selector, field_selector},
                      "score": float, "features": dict}, ...],
          "method": "quantum" | "classical_fallback"
        }
    """
    if not candidates:
        return {"ranked": [], "method": "classical_fallback"}

    field    = interpreted.get("field", "name")
    features = _compute_features(candidates, html, old_selectors, field)

    try:
        ranked_pairs = _qaoa_rank(candidates, features)
        method = "quantum"
        logger.info("QAOA ranking succeeded on %d candidates.", len(candidates))
    except ImportError:
        logger.warning("Qiskit not installed — classical fallback.")
        ranked_pairs = sorted(
            zip(candidates, [_classical_score(f) for f in features]),
            key=lambda x: x[1], reverse=True
        )
        method = "classical_fallback"
    except Exception as exc:
        logger.warning("QAOA failed (%s) — classical fallback.", exc)
        ranked_pairs = sorted(
            zip(candidates, [_classical_score(f) for f in features]),
            key=lambda x: x[1], reverse=True
        )
        method = "classical_fallback"

    feat_map = {
        (c["container_selector"], c["field_selector"]): f
        for c, f in zip(candidates, features)
    }

    return {
        "ranked": [
            {
                "candidate": cand,
                "score":     round(score, 4),
                "features":  feat_map.get(
                    (cand["container_selector"], cand["field_selector"]), {}
                ),
            }
            for cand, score in ranked_pairs
        ],
        "method": method,
    }
