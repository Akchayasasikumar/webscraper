# 🕷️ AI Self-Healing Web Scraper — Complete Project Guide

> This document explains **what the project does now**, **how it works step by step**, and **what can be added in the future** (next semester).  
> Written so anyone can understand it — no prior scraping knowledge needed.

---

## 📌 The Problem This Project Solves

Normal web scrapers are fragile. They use **CSS selectors** (like `.product .price`) hardcoded by a developer. When a website redesigns its HTML — which happens all the time — the scraper breaks silently and stops working.

**This project solves that problem** by building a scraper that:
- Understands plain English (no CSS knowledge needed)
- Finds its own selectors automatically
- Detects when it breaks
- Repairs itself without any human help

---

## ✅ What Currently Works (Phase 1 — Completed)

### Feature 1: Natural Language Query
```
You type:  "retrieve all the lipstick prices"
System understands:
  → field = "price"
  → filter = "lipstick" (only show lipstick products)
  → multiple = true (get all, not just one)
```
No CSS, no technical knowledge needed.

---

### Feature 2: Automatic Selector Discovery
The system **figures out CSS selectors by itself** by scanning the HTML DOM:
```
Step 1: Walk every element in the page
Step 2: Find elements whose text looks like a price (₹, $, Rs.)
Step 3: Walk up to find a repeating parent (the "product card")
Step 4: Score the candidate: class name match + text match + repetition count
Step 5: Return top 5 candidates
```
No human types `.product .price` — the machine finds it.

---

### Feature 3: Self-Healing Pipeline (10 Steps)

This is the **core feature**. When a website changes its HTML:

```
STEP 1  🌐  LOADING PAGE
            → Playwright browser loads the URL (handles JavaScript sites)

STEP 2  🔗  CONNECTED
            → Page loaded successfully

STEP 3  ⚡  SCRAPING
            → Checks SQLite database for a stored selector
            → If found, tries to use it

STEP 4  ⚠️  FAILURE DETECTED
            → Old selector returned 0 results?
            → Values wrong type (text instead of price)?
            → First time ever (cold start)?
            → Triggers self-healing

STEP 5  🔍  ANALYZING DOM
            → Reads the full HTML of the current page
            → Identifies repeating structures (product cards, list items)

STEP 6  🧠  GENERATING CANDIDATES
            → Produces 3–5 candidate selector pairs like:
               {container: "div.product-card", field: "div.cost"}
               {container: "li.grid__item",    field: "span.price-item--regular"}
            → Uses heuristic engine (always works)
            → OR uses Claude LLM if API key is set (smarter)

STEP 7  ⚛️  QUANTUM OPTIMIZATION
            → Scores each candidate using a real QAOA quantum circuit
            → Runs on Qiskit Aer local quantum simulator
            → Produces ranked list: best candidate first
            → Falls back to classical scoring if Qiskit not installed

STEP 8  🧪  VALIDATING
            → Tests each candidate on the live HTML
            → Checks: does it find elements? Do they look like prices?
            → First candidate that passes = winner

STEP 9  🔧  REPAIRED
            → Winning selector saved to SQLite database
            → Healing event logged to history

STEP 10 🚀  RESUMED
            → Extracts data using the new selector
            → Returns results to user
```

---

### Feature 4: Batch Mode
Upload a `.txt` file with multiple queries — one per line:
```
retrieve all the lipstick prices
get every product name on the page
show me foundation ratings
```
All 3 run automatically. Download results as **CSV file**.

---

### Feature 5: Live Dashboard (React Frontend)
| Panel | What It Shows |
|-------|--------------|
| **Pipeline Flow** | 10-step live stepper updating in real time |
| **Selector Comparison** | Old broken selector ❌ vs New working selector ✅ |
| **Candidate List** | All candidates with quantum scores |
| **Results Table** | Extracted data (prices, names, ratings) |
| **History Log** | Every past healing event from SQLite |

---

### Feature 6: Generic URL Support
```
Demo site URL:   http://localhost:8000/demo/products  → always works
External sites:  http://books.toscrape.com            → Playwright renders it
                 https://webscraper.io/test-sites/... → works
                 Amazon, Flipkart                     → blocked (bot protection)
```

---

## 🗂️ How Every File Works

```
selfhealing-scraper/
│
├── backend/
│   │
│   ├── main.py              → FastAPI server. All API endpoints live here.
│   │                          POST /scraper/query  — runs the pipeline
│   │                          GET  /scraper/status — frontend polls this every 1s
│   │                          POST /demo/simulate-change — switches HTML structure
│   │
│   ├── browser.py           → Playwright browser loader.
│   │                          For demo URL → returns demo HTML instantly
│   │                          For external URLs → opens headless Chrome, renders JS
│   │
│   ├── pipeline.py          → The brain. Orchestrates all 10 steps in order.
│   │                          Calls every other module in sequence.
│   │
│   ├── query_interpreter.py → Converts English → {field, filter_keyword, multiple}
│   │                          "lipstick prices" → {field:"price", filter:"lipstick"}
│   │
│   ├── scraper.py           → Given HTML + selector pair, extracts values.
│   │                          Returns list of matched items.
│   │
│   ├── failure_detector.py  → Decides if extraction failed.
│   │                          Checks: 0 results, wrong type, no selector stored.
│   │
│   ├── candidate_generator.py → Generates CSS selector candidates from DOM.
│   │                            Heuristic: walks HTML tree, scores by class names.
│   │                            LLM: asks Claude API (if key is set).
│   │
│   ├── quantum_optimizer.py → Ranks candidates using QAOA quantum circuit.
│   │                          Real Qiskit code: Hadamard, RZ, RX gates.
│   │                          Falls back to classical scoring if Qiskit missing.
│   │
│   ├── validator.py         → Tests if a candidate works on the live HTML.
│   │                          Verifies: elements found, values match type.
│   │
│   ├── database.py          → SQLite database manager.
│   │                          selector_store: saves winning selectors per URL+query
│   │                          healing_history: logs every repair event
│   │                          batch_results: stores batch query results for CSV
│   │
│   └── demo_site.py         → The controlled demo website (8 beauty products).
│                              Structure A: div.product → span.price
│                              Structure B: div.product-card → div.cost
│                              Clicking 💥 toggles between them.
│
└── frontend/src/
    ├── App.jsx              → Main app. Polls /scraper/status every 1 second.
    ├── api.js               → All HTTP calls to the backend.
    ├── components/
    │   ├── QueryInput.jsx        → URL input + text/file query toggle
    │   ├── PipelineFlow.jsx      → 10-step visual stepper
    │   ├── SelectorComparison.jsx→ Shows old selector vs new selector
    │   ├── CandidateList.jsx     → Table of candidates + quantum scores
    │   ├── ResultsTable.jsx      → Results + CSV download button
    │   └── HistoryLog.jsx        → Healing history from SQLite
```

---

## 🔬 The Quantum Part — Explained Simply

> ❓ *"Is it actually quantum?"*  
> ✅ Yes — it runs a **real quantum circuit** on a **local quantum simulator**.

```
What the quantum part does:
  - Takes the 5 candidate selectors as input
  - Each candidate gets 1 qubit
  - Builds a QAOA circuit with Hadamard + RZ + RX gates
  - Runs it on the Qiskit Aer statevector simulator
  - Measures which qubit has the highest probability of being |1⟩
  - That candidate is ranked highest

What quantum is NOT doing here:
  - It is NOT browsing the internet
  - It is NOT magically knowing which selector is correct
  - It is NOT running on real quantum hardware (IBM/Google)
  - It is a local SIMULATOR — same math, no real qubits needed

Why use quantum at all:
  - Demonstrates QAOA (Quantum Approximate Optimization Algorithm)
  - This is the same algorithm used for real optimization problems
  - For a college project, running on a simulator is the correct approach
```

---

## 🚧 Future Implementations (Next Semester — Phase 2)

These features are **planned but not built yet**. Listed in order of priority:

---

### 🔜 Priority 1: Smarter Name/Text Extraction
**Problem now:** The system extracts prices well (they have `₹`/`$` patterns) but struggles with product names (any text could be a name).

**Future fix:**
```
Step 1: Use Claude LLM to look at a snippet of the DOM
Step 2: Ask it: "Which element contains the product name?"
Step 3: Claude identifies: "h3.card__heading > a"
Step 4: Use that as the field selector
```
**File to edit:** `candidate_generator.py` → `_llm_candidates()` function

---

### 🔜 Priority 2: Visual Screenshot on Healing
**Problem now:** When healing happens, users only see text selectors. 

**Future fix:** Take a Playwright screenshot of the page before and after healing, display it side-by-side in the dashboard.

```
After healing → show:
  [Screenshot with OLD selector highlighted in red]
  [Screenshot with NEW selector highlighted in green]
```
**Files to add:** `browser.py` (add screenshot function) + new React component `HealingScreenshot.jsx`

---

### 🔜 Priority 3: Scheduled Auto-Scraping
**Problem now:** User has to manually click Run every time.

**Future fix:** Add a scheduler — user sets a URL + query + interval (e.g., every 6 hours). The system scrapes automatically and emails results if it healed.

```
User sets:
  URL: http://books.toscrape.com
  Query: get all book prices
  Schedule: every 6 hours
  Alert: email me if the selector healed

System runs automatically, emails when something changes.
```
**Files to add:** `scheduler.py` (APScheduler library) + new API endpoints

---

### 🔜 Priority 4: Multi-Page Scraping (Pagination)
**Problem now:** Only scrapes the first page of a site.

**Future fix:** Detect "Next Page" or pagination links, follow them, and scrape all pages.

```
books.toscrape.com has 50 pages of books.
Currently: only gets 20 books from page 1
Future: follows "next →" link, gets all 1000 books
```
**File to edit:** `browser.py` + `pipeline.py`

---

### 🔜 Priority 5: Real Quantum Hardware (IBM Q)
**Problem now:** Quantum circuit runs on a local simulator (Qiskit Aer).

**Future fix:** Connect to **IBM Quantum** real hardware via IBM Cloud API. Run the QAOA circuit on actual quantum bits.

```
Current:  Qiskit Aer Simulator (local, free, instant)
Future:   IBM Quantum hardware (cloud, free tier available)
          → Connect via IBMQ account + API token
          → Queue the job, wait for real quantum computer results
```
**File to edit:** `quantum_optimizer.py` — add IBMQ backend option

---

### 🔜 Priority 6: Export to More Formats
**Problem now:** Only CSV download available.

**Future fix:** Add JSON, Excel (.xlsx), and Google Sheets export.

```
Current options:  ⬇ Download CSV
Future options:   ⬇ Download CSV
                  ⬇ Download JSON
                  ⬇ Download Excel
                  📤 Send to Google Sheets
```
**File to edit:** `main.py` (new download endpoints) + `ResultsTable.jsx`

---

### 🔜 Priority 7: User Accounts + Saved Projects
**Problem now:** No login — everyone shares the same state.

**Future fix:** Add user authentication (JWT), so each user has their own:
- Saved URL + query combinations
- Their own healing history
- Private batch results

```
Tech stack addition:
  Backend: JWT authentication (python-jose library)
  Database: Add users table to SQLite
  Frontend: Login page + user dashboard
```

---

### 🔜 Priority 8: Browser Extension
**Problem now:** Users copy-paste URLs into the app.

**Future fix:** Build a Chrome/Firefox extension — user clicks a button while browsing, the extension sends the current page URL + selected text as the query.

```
User is on books.toscrape.com
Selects some text → right-clicks → "Scrape with Self-Healer"
Extension sends URL to the scraper API automatically
```

---

## 📊 Current vs Future Comparison

| Feature | Now (Phase 1) | Future (Phase 2) |
|---------|--------------|-----------------|
| Query input | Text box | Text + voice + browser extension |
| Page loading | Playwright (1 page) | Multi-page + pagination |
| Selector finding | Heuristic + optional LLM | Full LLM semantic analysis |
| Quantum | Local simulator | Real IBM Quantum hardware |
| Scheduling | Manual run | Auto-scheduled with email alerts |
| Export | CSV only | CSV + JSON + Excel + Google Sheets |
| Users | Single user | Multi-user with accounts |
| Visualization | Text selectors | Screenshots + highlights |

---

## 🧑‍💻 Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React + Vite | Fast, component-based UI |
| Styling | Vanilla CSS | No framework needed |
| Backend | FastAPI (Python) | Fast, auto-generates API docs |
| Server | Uvicorn | ASGI server for FastAPI |
| Web Scraping | BeautifulSoup4 + lxml | HTML parsing |
| Browser | Playwright (Chromium) | JavaScript rendering |
| Quantum | Qiskit + Qiskit-Aer | QAOA circuit simulation |
| LLM | Anthropic Claude (optional) | Semantic DOM analysis |
| Database | SQLite3 | Built into Python, no setup |

---

## 🔁 Complete Data Flow (For Friends)

```
[User types URL + Query]
        │
        ▼
[Frontend sends POST /scraper/query]
        │
        ▼
[browser.py loads the page]
  ├── Demo URL? → return demo HTML instantly
  └── External? → Playwright opens Chrome, renders JS, returns HTML
        │
        ▼
[query_interpreter.py]
  "get all jersey prices" → {field:"price", filter:None, multiple:True}
        │
        ▼
[database.py: get_selectors()]
  Has a stored selector for this URL+query? 
  ├── YES → try it → [scraper.py extracts data]
  │               → [failure_detector.py checks] → OK? → return results ✅
  │
  └── NO or FAILED → Self-Healing Pipeline starts
        │
        ▼
[candidate_generator.py]
  Walk DOM → score elements → return 5 candidates
        │
        ▼
[quantum_optimizer.py]
  QAOA circuit → rank candidates by probability
        │
        ▼
[validator.py]
  Test each candidate on real HTML → pick first that works
        │
        ▼
[database.py: save_selectors()]
  Save winning selector to SQLite
        │
        ▼
[scraper.py: extract_filtered()]
  Extract all matching items → return list
        │
        ▼
[Frontend receives result]
  Pipeline stepper updates → Results shown → History logged
```

---


