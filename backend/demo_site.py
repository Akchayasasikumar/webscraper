"""
demo_site.py — Product listing page in two HTML structures.

Products: 3 lipsticks, 3 foundations, 2 serums (8 items total).
Structure A: <div class="product"><span class="name">...</span><span class="price">...</span><span class="rating">...</span></div>
Structure B: <div class="product-card"><div class="title">...</div><div class="cost">...</div><div class="stars">...</div></div>

Same data, renamed classes — toggling simulates a "website redesign" that breaks selectors.
"""

_current_structure: str = "A"

# ── Product data ─────────────────────────────────────────────────────────────
PRODUCTS = [
    {"id": 1, "category": "lipstick", "name": "Maybelline SuperStay Matte Ink",      "price": "₹599",   "rating": "4.5"},
    {"id": 2, "category": "lipstick", "name": "Lakme 9 to 5 Primer + Matte",          "price": "₹449",   "rating": "4.2"},
    {"id": 3, "category": "lipstick", "name": "L'Oreal Paris Color Riche",            "price": "₹749",   "rating": "4.6"},
    {"id": 4, "category": "foundation","name": "MAC Studio Fix Fluid Foundation",      "price": "₹3,299", "rating": "4.7"},
    {"id": 5, "category": "foundation","name": "Lakme Invisible Finish Foundation",    "price": "₹329",   "rating": "3.9"},
    {"id": 6, "category": "foundation","name": "Maybelline Fit Me Matte + Poreless",  "price": "₹449",   "rating": "4.3"},
    {"id": 7, "category": "serum",     "name": "Minimalist 10% Niacinamide Serum",   "price": "₹599",   "rating": "4.8"},
    {"id": 8, "category": "serum",     "name": "Plum 15% Vitamin C Serum",           "price": "₹899",   "rating": "4.4"},
]


def toggle_structure() -> str:
    global _current_structure
    _current_structure = "B" if _current_structure == "A" else "A"
    return _current_structure


def get_current_structure() -> str:
    return _current_structure


def reset_structure() -> None:
    global _current_structure
    _current_structure = "A"


def _render_structure_a() -> str:
    items_html = "\n".join(
        f'''    <div class="product" data-category="{p['category']}">
      <span class="name">{p['name']}</span>
      <span class="price">{p['price']}</span>
      <span class="rating">{p['rating']}</span>
      <span class="category-tag">{p['category']}</span>
    </div>'''
        for p in PRODUCTS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BeautyShop — Products (v1)</title>
  <style>
    body {{ font-family: sans-serif; max-width: 900px; margin: 40px auto; }}
    .product {{ border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 4px; }}
    .name {{ font-weight: bold; display: block; }}
    .price {{ color: #c00; margin: 4px 8px 0 0; }}
    .rating {{ color: #f90; }}
    .category-tag {{ color: #888; font-size: 0.85em; margin-left: 8px; }}
  </style>
</head>
<body>
  <h1>Beauty Products</h1>
  <p>Structure: A — <em>initial design</em></p>
  <section class="product-list">
{items_html}
  </section>
</body>
</html>"""


def _render_structure_b() -> str:
    items_html = "\n".join(
        f'''    <div class="product-card" data-cat="{p['category']}">
      <div class="title">{p['name']}</div>
      <div class="cost">{p['price']}</div>
      <div class="stars">{p['rating']}</div>
      <div class="product-type">{p['category']}</div>
    </div>'''
        for p in PRODUCTS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BeautyShop — Products (v2)</title>
  <style>
    body {{ font-family: sans-serif; max-width: 900px; margin: 40px auto; }}
    .product-card {{ border: 1px solid #bbb; padding: 16px; margin: 10px 0; border-radius: 8px; background: #fafafa; }}
    .title {{ font-weight: 700; font-size: 1.05em; }}
    .cost {{ color: #d00; margin-top: 6px; }}
    .stars {{ color: #fa0; margin-top: 4px; }}
    .product-type {{ color: #999; font-size: 0.82em; margin-top: 4px; }}
  </style>
</head>
<body>
  <h1>Beauty Products</h1>
  <p>Structure: B — <em>redesigned</em></p>
  <section class="products-grid">
{items_html}
  </section>
</body>
</html>"""


def get_demo_html() -> str:
    return _render_structure_a() if _current_structure == "A" else _render_structure_b()


# Known correct selectors for each structure (used in tests)
SELECTOR_MAP = {
    "A": {
        "container": ".product",
        "price":     ".price",
        "name":      ".name",
        "rating":    ".rating",
    },
    "B": {
        "container": ".product-card",
        "price":     ".cost",
        "name":      ".title",
        "rating":    ".stars",
    },
}
