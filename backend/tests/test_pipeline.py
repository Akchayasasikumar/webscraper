"""
test_pipeline.py — End-to-end integration tests.
Run: python -X utf8 tests/test_pipeline.py
"""
import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from demo_site import (
    PRODUCTS, SELECTOR_MAP,
    _render_structure_a, _render_structure_b,
    toggle_structure, reset_structure,
)
from database import init_db, get_selectors, save_selectors, get_history
from query_interpreter import interpret
from scraper import extract, extract_filtered
from failure_detector import is_failure
from candidate_generator import generate_candidates
from quantum_optimizer import rank_candidates
from validator import validate
from pipeline import run_query


HTML_A = _render_structure_a()
HTML_B = _render_structure_b()

DEMO_URL = "http://localhost:8000/demo/products"


def banner(msg: str):
    print(f"\n{'='*60}\n{msg}\n{'='*60}")


def test_query_interpreter():
    banner("TEST: Query Interpreter")
    r1 = interpret("retrieve all the lipstick prices")
    assert r1["field"] == "price", f"Expected field=price, got {r1['field']}"
    assert r1["filter_keyword"] == "lipstick", f"Expected filter=lipstick, got {r1['filter_keyword']}"
    assert r1["multiple"] == True
    print("  ✓ 'retrieve all the lipstick prices' ->", r1)

    r2 = interpret("get every product name on the page")
    assert r2["field"] == "name", f"Expected field=name, got {r2['field']}"
    assert r2["multiple"] == True
    print("  ✓ 'get every product name on the page' ->", r2)

    r3 = interpret("show me foundation ratings")
    assert r3["field"] == "rating", f"Expected field=rating, got {r3['field']}"
    print("  ✓ 'show me foundation ratings' ->", r3)


def test_scraper_structure_a():
    banner("TEST: Scraper on Structure A")
    cs = SELECTOR_MAP["A"]["container"]
    fs = SELECTOR_MAP["A"]["price"]
    items = extract(HTML_A, cs, fs, filter_keyword="lipstick")
    matched = [r["text"] for r in items if r["matched"] and r["text"]]
    print(f"  Lipstick prices from A: {matched}")
    assert len(matched) == 3, f"Expected 3 lipstick prices, got {len(matched)}: {matched}"
    print("  ✓ Correct count")

    # Structure A selectors fail on structure B
    items_b = extract(HTML_B, cs, fs, filter_keyword="lipstick")
    matched_b = [r["text"] for r in items_b if r["matched"] and r["text"]]
    failed, reason = is_failure(items_b, {"field": "price", "filter_keyword": "lipstick", "multiple": True}, cs, fs)
    print(f"  Structure A selectors on B → matched={matched_b}, failed={failed}")
    assert failed, "Expected failure when using A selectors on B HTML"
    print("  ✓ Failure correctly detected")


def test_candidate_generator():
    banner("TEST: Candidate Generator (Structure B)")
    interpreted = {"field": "price", "filter_keyword": "lipstick", "multiple": True}
    old_sel = {
        "container_selector": SELECTOR_MAP["A"]["container"],
        "field_selector":     SELECTOR_MAP["A"]["price"],
    }
    gen = generate_candidates(HTML_B, interpreted, old_sel)
    candidates = gen["candidates"]
    print(f"  Source: {gen['source']}, Candidates: {len(candidates)}")
    for c in candidates:
        print(f"    {c}")

    # .product-card with .cost equivalent must appear
    found = any(
        "product-card" in c["container_selector"] or "product-card" in c["container_selector"]
        for c in candidates
    ) or any(
        "cost" in c["field_selector"] for c in candidates
    )
    assert found, f"Expected .product-card or .cost in candidates: {candidates}"
    print("  ✓ Found expected container/field selectors")


def test_quantum_optimizer():
    banner("TEST: Quantum Optimizer")
    interpreted = {"field": "price", "filter_keyword": "lipstick", "multiple": True}
    old_sel = {
        "container_selector": SELECTOR_MAP["A"]["container"],
        "field_selector":     SELECTOR_MAP["A"]["price"],
    }
    gen = generate_candidates(HTML_B, interpreted, old_sel)
    candidates = gen["candidates"]
    result = rank_candidates(candidates, HTML_B, interpreted, old_sel)
    print(f"  Method: {result['method']}")
    for r in result["ranked"]:
        print(f"    {r['score']:.4f}  {r['candidate']}")
    assert "method" in result
    assert len(result["ranked"]) > 0
    print("  ✓ Ranking succeeded, method field present")


def test_full_pipeline():
    banner("TEST: Full Pipeline — Cold Start on Structure A")
    init_db()
    state = {
        "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
        "current_query": "", "interpreted": {}, "last_items": [],
        "new_selectors": None, "error": None,
    }

    query = "retrieve all the lipstick prices"
    result = run_query(DEMO_URL, query, HTML_A, state)
    print(f"  Status: {result['final_status']}")
    print(f"  Items: {result['items']}")

    assert result["final_status"] in ("ok", "healed"), f"Expected ok/healed, got: {result['final_status']}"
    assert len(result["items"]) == 3, f"Expected 3 lipstick prices, got: {result['items']}"
    print("  ✓ Cold start passed, 3 lipstick prices extracted")

    # Verify selector was saved
    saved = get_selectors(DEMO_URL, query)
    assert saved, "Selector should have been saved to DB"
    print(f"  ✓ Selectors persisted: {saved}")


def test_healing_pipeline():
    banner("TEST: Healing — Structure Change A → B")
    init_db()
    state = {
        "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
        "current_query": "", "interpreted": {}, "last_items": [],
        "new_selectors": None, "error": None,
    }

    query = "retrieve all the lipstick prices"

    # First, ensure A selectors are stored (run on A)
    run_query(DEMO_URL, query, HTML_A, state)

    # Now simulate website change → run same query on B HTML
    print("\n  [Simulating website change to structure B...]")
    state2 = {
        "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
        "current_query": "", "interpreted": {}, "last_items": [],
        "new_selectors": None, "error": None,
    }
    result = run_query(DEMO_URL, query, HTML_B, state2)
    print(f"  Final status: {result['final_status']}")
    print(f"  Old selectors: {result['old_selectors']}")
    print(f"  New selectors: {result['new_selectors']}")
    print(f"  Items: {result['items']}")

    assert result["final_status"] == "healed", f"Expected 'healed', got: {result['final_status']}"
    assert len(result["items"]) > 0, "Should have extracted some items after healing"
    print("  ✓ Pipeline healed from A to B selectors!")


def test_batch():
    banner("TEST: Batch — Multiple Queries")
    init_db()
    queries = [
        "retrieve all the lipstick prices",
        "get every product name on the page",
        "show me foundation ratings",
    ]
    print(f"  Running {len(queries)} queries on structure A HTML...")
    for q in queries:
        state = {
            "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
            "current_query": "", "interpreted": {}, "last_items": [],
            "new_selectors": None, "error": None,
        }
        result = run_query(DEMO_URL, q, HTML_A, state)
        print(f"  [{result['final_status']}] '{q}' → {result['items'][:3]}...")
        assert result["final_status"] in ("ok", "healed"), f"Query failed: {q}"
        assert len(result["items"]) > 0, f"No items for: {q}"
    print("  ✓ All batch queries returned items")


if __name__ == "__main__":
    test_query_interpreter()
    test_scraper_structure_a()
    test_candidate_generator()
    test_quantum_optimizer()
    test_full_pipeline()
    test_healing_pipeline()
    test_batch()

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
