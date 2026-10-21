"""
test_pipeline.py — End-to-end integration tests.
Run: python -X utf8 tests/test_pipeline.py
"""
import sys, os
from unittest.mock import patch
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

MYNTRA_HTML = """
<html><body>
  <nav class="desktop-navContent">
    <span>Rs. 99</span><span>50% OFF</span><span>Delivery in 2 days</span>
  </nav>
  <ul>
    <li class="product-base">
      <div class="product-ratingsContainer">4.2 | 10</div>
      <div class="product-price"><span>Rs. 579</span></div>
    </li>
    <li class="product-base">
      <div class="product-ratingsContainer">4.6 | 1.5k</div>
      <div class="product-price">
        <span>
          <span class="product-discountedPrice">Rs. 719</span>
          <span class="product-strike">Rs. 1199</span>
        </span>
        <span class="product-discountPercentage">(Rs. 480 OFF)</span>
      </div>
    </li>
    <li class="product-base">
      <div class="product-ratingsContainer">4.4 | 7k</div>
      <div class="product-price">
        <span>
          <span class="product-discountedPrice">Rs. 284</span>
          <span class="product-strike">Rs. 999</span>
        </span>
        <span class="product-discountPercentage">(72% OFF)</span>
      </div>
    </li>
  </ul>
  <aside>Rs. 500 delivery charge</aside>
</body></html>
"""


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

    r4 = interpret("Retrieve all product prices on this page")
    assert r4["field"] == "price", f"Expected field=price, got {r4['field']}"
    assert r4["filter_keyword"] is None, f"Expected no filter, got {r4['filter_keyword']}"
    assert r4["multiple"] is True
    print("  ✓ Myntra query has no accidental filter ->", r4)

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
        with patch(
            "query_interpreter._llm_interpret",
            return_value={"field": "price", "filter_keyword": "this", "multiple": True},
        ):
            llm_result = interpret("Retrieve all product prices on this page")
    assert llm_result["filter_keyword"] is None, llm_result
    print("  ✓ LLM stop-word filter is discarded")


def test_myntra_product_prices():
    banner("TEST: Myntra Product Price Extraction")
    query = "Retrieve all product prices on this page"
    interpreted = interpret(query)
    generated = generate_candidates(MYNTRA_HTML, interpreted, {})
    candidate = next(
        (
            item for item in generated["candidates"]
            if item["container_selector"] == "li.product-base"
        ),
        None,
    )
    assert candidate, f"Expected a product-card candidate: {generated['candidates']}"
    name_candidates = generate_candidates(MYNTRA_HTML, {"field": "name"}, {})
    assert not any(
        item.get("field_selector", "").startswith(".product-discountedPrice")
        for item in name_candidates["candidates"]
    ), "Price-specific selectors must not be used for name queries"

    validation = validate(MYNTRA_HTML, candidate, interpreted)
    assert validation["valid"], validation["reason"]
    assert validation["count"] == 3, validation

    raw = extract(
        MYNTRA_HTML,
        candidate["container_selector"],
        candidate["field_selector"],
        interpreted["filter_keyword"],
    )
    failed, reason = is_failure(
        raw,
        interpreted,
        candidate["container_selector"],
        candidate["field_selector"],
    )
    assert not failed, reason
    items = extract_filtered(
        MYNTRA_HTML,
        candidate["container_selector"],
        candidate["field_selector"],
        interpreted["filter_keyword"],
    )
    expected = ["Rs. 579", "Rs. 719", "Rs. 284"]
    assert items == expected, f"Expected current product prices {expected}, got {items}"
    print("  ✓ Product-only prices extracted; navigation, rating, MRP and discount values excluded")

    init_db()
    state = {
        "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
        "current_query": "", "interpreted": {}, "last_items": [],
        "new_selectors": None, "error": None,
    }
    url = "https://www.myntra.com/myntra-fashion-store?f=product-list"
    first = run_query(url, query, MYNTRA_HTML, state)
    assert first["final_status"] == "healed", first
    assert first["items"] == expected, first["items"]

    second_state = {
        "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
        "current_query": "", "interpreted": {}, "last_items": [],
        "new_selectors": None, "error": None,
    }
    second = run_query(url, query, MYNTRA_HTML, second_state)
    assert second["final_status"] == "ok", second
    assert second["items"] == expected, second["items"]
    print("  ✓ Self-healed selector is reused for subsequent extraction")

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
    test_myntra_product_prices()
    test_scraper_structure_a()
    test_candidate_generator()
    test_quantum_optimizer()
    test_full_pipeline()
    test_healing_pipeline()
    test_batch()

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
