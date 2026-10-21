# AI-Powered Self-Healing Web Scraper with Quantum-Assisted Optimization

> A college project — a web scraper that **understands plain English**, **finds its own CSS selectors**, and **automatically repairs itself** when a website's HTML structure changes, without any human intervention.

---

## 🧠 What It Does

Traditional scrapers break silently when a website is redesigned. This project solves that:

| Step | What Happens |
|------|-------------|
| **1. Understand** | User types a plain-English query like *"retrieve all the lipstick prices"* — no CSS knowledge needed |
| **2. Load Page** | Playwright headless browser loads the page (handles JavaScript-rendered sites) |
| **3. Extract** | Uses stored CSS selectors to extract the data |
| **4. Detect** | Automatically detects if extraction failed (0 results, wrong type, first run) |
| **5. Heal** | Generates new candidate selectors by analyzing the DOM |
| **6. Optimize** | Uses a **real QAOA quantum circuit** (via Qiskit) to rank the candidates |
| **7. Validate** | Tests each candidate against the live page — picks the first one that works |
| **8. Resume** | Saves the winning selector to SQLite and returns the data |

---

## ✨ Key Features

- 🗣️ **Natural Language Queries** — type what you want in plain English
- ⚛️ **Quantum Optimization** — real QAOA circuit on Qiskit Aer simulator ranks candidates (falls back to classical scoring if Qiskit not installed)
- 🔧 **Self-Healing Pipeline** — 10-step automated repair loop
- 🌐 **Generic URL Support** — works on any publicly accessible website via Playwright
- 📄 **Batch Mode** — upload a `.txt` file with multiple queries, download results as CSV
- 🗄️ **SQLite History** — every healing event is logged permanently
- 🖥️ **Live Dashboard** — React frontend with real-time pipeline stepper, selector comparison, and candidate scores

---

## 🏗️ Architecture

```
┌──────────────── React Frontend (Vite · port 5173) ─────────────────┐
│                                                                      │
│   QueryInput    →   PipelineFlow    →   SelectorComparison          │
│   (text/batch)      (10-step live)      (old ❌  →  new ✅)         │
│                                                                      │
│   CandidateList  →  ResultsTable   →   HistoryLog                   │
│   (quantum scores)  (results+CSV)      (SQLite log)                  │
│                                                                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  HTTP / JSON  (polling every 1s)
┌─────────────────────────────▼───────────────────────────────────────┐
│              FastAPI Backend (Uvicorn · port 8000)                   │
│                                                                      │
│   browser.py           Playwright page loader (JS rendering)         │
│   query_interpreter.py  NL query → {field, filter_keyword, multiple} │
│   scraper.py            Container + field list-aware extraction       │
│   failure_detector.py   Cold start / 0 results / type mismatch       │
│   candidate_generator.py Heuristic DOM analysis + optional Claude    │
│   quantum_optimizer.py  Qiskit QAOA circuit + classical fallback     │
│   validator.py          Confirm selector works on live DOM            │
│   database.py           SQLite: selector_store + healing_history      │
│   pipeline.py           Orchestrates the full 10-step loop            │
│   demo_site.py          Controlled 8-product demo page (2 structures) │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Requirements
- Python **3.11+**
- Node.js **18+**
- npm

---

### Step 1 — Clone the repo
```bash
git clone https://github.com/your-username/selfhealing-scraper.git
cd selfhealing-scraper
```

---

### Step 2 — Set up the Backend

```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
```

Start the backend server:
```bash
uvicorn main:app --reload
```

Backend runs at → **http://localhost:8000**  
API docs at → **http://localhost:8000/docs**

---

### Step 3 — Set up the Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at → **http://localhost:5173**

---

### Step 4 — Open the App

Open your browser and go to:
```
http://localhost:5173
```

> ⚠️ Always start the **backend first**, then the frontend.

---

## 🎬 Demo Walkthrough

### Part 1 — Normal Scraping

1. URL is pre-filled as `http://localhost:8000/demo/products`
2. Type in the query box: **`retrieve all the lipstick prices`**
3. Click **▶ Run Query**
4. Result: `₹599`, `₹449`, `₹749` extracted automatically ✅

### Part 2 — Self-Healing (Main Feature)

5. Click **💥 Simulate Website Change** — this changes the demo site's HTML structure (class names renamed)
6. Click **▶ Run Query** again with the **same query**
7. Watch the pipeline:
   - ⚠️ Old selector **fails** (class names changed)
   - 🔍 DOM is **analyzed**
   - 🧠 New **candidates generated**
   - ⚛️ **Quantum optimizer** ranks them
   - ✅ Best candidate **validated** and saved
   - 🚀 Same results returned: `₹599`, `₹449`, `₹749`

### Part 3 — Batch Mode

8. Create a file `queries.txt`:
   ```
   retrieve all the lipstick prices
   get every product name on the page
   show me foundation ratings
   ```
9. Click **📄 Upload batch file**, select the file, click **▶ Run Batch**
10. Click **⬇ Download CSV** to get all results as a spreadsheet

---

## 🧪 Running Tests

```bash
cd backend
python -X utf8 tests/test_pipeline.py
```

Expected output:
```
TEST: Query Interpreter          ✓
TEST: Scraper on Structure A     ✓
TEST: Candidate Generator        ✓
TEST: Quantum Optimizer          ✓
TEST: Full Pipeline — Cold Start ✓
TEST: Healing — Structure A → B  ✓
TEST: Batch — Multiple Queries   ✓

ALL TESTS PASSED ✓
```

---

## ⚙️ Optional Configuration

### Enable Quantum Ranking (Qiskit)

Without Qiskit, candidates are ranked using classical scoring — the system still heals correctly.
To enable real quantum QAOA ranking:

```bash
pip install qiskit==1.1.0 qiskit-aer==0.14.1
```

### Enable LLM Support (Claude API)

Without a Claude API key, the system uses built-in heuristic engines — everything still works.
To enable Claude for smarter query interpretation and selector generation:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# Mac / Linux
export ANTHROPIC_API_KEY=sk-ant-...

pip install anthropic
```

---

## 📁 File Structure

```
selfhealing-scraper/
│
├── README.md
│
├── backend/
│   ├── requirements.txt          Python dependencies
│   ├── .env.example              Example environment variables
│   │
│   ├── main.py                   FastAPI app — all API endpoints
│   ├── browser.py                Playwright page loader
│   ├── pipeline.py               10-step orchestrator (DETECT → RESUME)
│   ├── query_interpreter.py      English query → {field, filter, multiple}
│   ├── scraper.py                Container + field CSS extraction
│   ├── failure_detector.py       Detects extraction failures
│   ├── candidate_generator.py    Generates CSS selector candidates
│   ├── quantum_optimizer.py      Qiskit QAOA + classical fallback
│   ├── validator.py              Validates candidates on live DOM
│   ├── database.py               SQLite: selectors + history
│   ├── demo_site.py              8-product demo page (Structure A & B)
│   │
│   └── tests/
│       └── test_pipeline.py      End-to-end integration tests
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx
        ├── App.jsx               Main app + polling logic
        ├── api.js                API client functions
        ├── index.css             Global styles
        │
        └── components/
            ├── QueryInput.jsx        URL + text/file input
            ├── PipelineFlow.jsx      Live 10-step pipeline stepper
            ├── SelectorComparison.jsx Old ❌ → New ✅ selector diff
            ├── CandidateList.jsx     Candidate scores table
            ├── ResultsTable.jsx      Results + CSV download
            └── HistoryLog.jsx        SQLite healing history log
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scraper/query` | Run pipeline for a single query |
| `POST` | `/scraper/batch` | Upload `.txt` file for batch queries |
| `GET`  | `/scraper/batch/{id}/download` | Download batch results as CSV |
| `GET`  | `/scraper/status` | Current pipeline state (polled by frontend) |
| `GET`  | `/scraper/history` | Full healing history from SQLite |
| `POST` | `/demo/simulate-change` | Toggle demo site structure A ↔ B |
| `GET`  | `/demo/products` | View current demo page HTML |
| `GET`  | `/demo/structure` | Current demo structure name (A or B) |
| `GET`  | `/health` | Server liveness check |

---

## ⚠️ Honest Limitations

- **Amazon, Flipkart, Myntra** — blocked by bot protection (Cloudflare, CAPTCHA). This is expected and by design — the project does not attempt any illegal bypass.
- **Login-required sites** — not supported.
- **Name field on complex sites** — heuristic name detection is less reliable than price detection (prices have unique patterns like `₹`/`Rs.`/`$`). Enable Claude API for better accuracy on real sites.
- **Quantum component** — runs on a **local quantum simulator** (Qiskit Aer), not real quantum hardware. This is standard practice for quantum algorithm demonstrations.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
# Self-Healing Web Scraper

## Abstract

This project is a web application for extracting structured values from web pages using natural-language queries. It detects when a saved CSS selector no longer returns suitable data, generates replacement selector candidates, ranks and validates them, and stores successful replacements. A React interface supports individual and batch jobs and displays pipeline status and extraction history.

## Problem Statement

Web scrapers that depend on fixed CSS selectors can stop returning useful data when a page structure changes. Detecting and repairing these failures manually requires inspecting the updated page and changing the selectors. This project explores an automated workflow for identifying such failures and attempting selector repair.

## Objectives

- Interpret plain-language requests as a target field and optional item filter.
- Extract values from repeating page elements using CSS selectors.
- Detect missing, empty, or type-inconsistent extraction results.
- Generate, rank, and validate alternative selectors after a detected failure.
- Persist selectors and per-user run history in SQLite.
- Provide a dashboard for single queries, batch queries, results, and pipeline activity.

## Proposed Methodology

For each request, the backend loads the target page and interprets the query. It first tries the selectors stored for that URL and query. If extraction is judged to have failed, it analyzes the page DOM and generates candidate container and field selectors. Candidate ranking uses weighted classical features by default; a Qiskit Aer circuit is an optional ranking path. The backend validates ranked candidates against the page, stores a candidate that passes validation, and records the run in SQLite.

## System Architecture and Workflow

The React/Vite frontend sends HTTP requests to the FastAPI backend. The frontend polls the authenticated status and history endpoints while a job runs. The backend loads page HTML, runs the extraction and repair pipeline, and uses SQLite for user accounts, selectors, job history, and batch results.

```text
React + Vite UI
     | HTTP / JSON
     v
FastAPI application (Uvicorn)
     |
     +--> Load page: demo HTML or Playwright, with an HTTP fallback
     +--> Interpret query and try saved selectors
     +--> Detect extraction failure
     +--> Generate and rank candidate selectors
     +--> Validate candidate and save successful selectors
     |
     +--> SQLite: users, selectors, history, and batch results
```

The pipeline stages exposed by the backend are `LOADING_PAGE`, `CONNECTED`, `SCRAPING`, `FAILURE_DETECTED`, `ANALYZING`, `GENERATING_CANDIDATES`, `OPTIMIZING`, `VALIDATING`, `REPAIRED`, and `RESUMED`.

## Technologies Used

| Area | Technology |
|---|---|
| Frontend | React 19, Vite 8, JavaScript, CSS |
| Backend API | Python, FastAPI, Uvicorn, Pydantic |
| HTML loading and parsing | Playwright, Requests, Beautiful Soup, lxml |
| Persistence | SQLite |
| Optional candidate ranking | Qiskit and Qiskit Aer |
| Optional language-model integration | Anthropic API |

Qiskit and Anthropic are not installed by the default requirements file. Without them, candidate ranking and query/candidate generation use the implemented classical and heuristic fallbacks.

## Key Features

- Natural-language requests for product names, prices, ratings, and filtered items.
- Selector reuse and automatic recovery attempts when extraction fails.
- Demo product page with two HTML structures to simulate selector-breaking changes.
- Account registration and sign-in; scraper operations and history are authenticated.
- Batch query upload from a plain-text file and CSV download of results.
- Dashboard views for pipeline status, candidate rankings, selector comparison, results, and history.
- Optional Qiskit-based candidate ranking and optional Anthropic-based interpretation and candidate generation.

## Project Structure

```text
webscraper/
├── README.md
├── backend/
│   ├── main.py                 FastAPI routes and application startup
│   ├── auth.py                 Password hashing and bearer-token handling
│   ├── browser.py              Page loading with Playwright and Requests fallback
│   ├── pipeline.py             Extraction, detection, repair, and persistence flow
│   ├── query_interpreter.py    Query-to-field and filter interpretation
│   ├── scraper.py              CSS-selector-based data extraction
│   ├── failure_detector.py     Extraction failure checks
│   ├── candidate_generator.py  Candidate selector generation
│   ├── quantum_optimizer.py   Candidate ranking and classical fallback
│   ├── validator.py            Candidate selector validation
│   ├── database.py              SQLite schema and data operations
│   ├── demo_site.py             Product data and alternate HTML structures
│   ├── requirements.txt         Python dependencies
│   └── tests/test_pipeline.py    Pipeline and demo-site tests
└── frontend/
   ├── package.json
   ├── package-lock.json
   ├── vite.config.js
   └── src/
      ├── App.jsx               Application views and authentication UI
      ├── api.js                Backend API client
      └── components/           Query, pipeline, result, and history views
```

## Installation and Setup

Prerequisites:

- Python 3.10 or later.
- Node.js `^20.19.0` or `>=22.12.0` and npm, as required by the locked Vite toolchain.

From the project root, create and install the backend environment. In Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

If PowerShell script activation is unavailable, use the environment's Python executable directly or activate the virtual environment using the command for your shell.

Install frontend dependencies in a second terminal from the project root:

```powershell
cd frontend
npm ci
```

### Optional Integrations

To enable Qiskit candidate ranking, install `qiskit` and `qiskit-aer` in the backend environment. Otherwise the application uses classical weighted scoring.

To enable the Anthropic integration, install the `anthropic` Python package and set `ANTHROPIC_API_KEY` in the backend process environment. Without the key, the application uses its heuristic engines.

## How to Run the Project

Start the backend from the `backend` directory:

```powershell
uvicorn main:app --reload --port 8000
```

Start the frontend in a second terminal from the `frontend` directory:

```powershel
npm run dev
```

Open `http://localhost:5173`, create an account or sign in, and submit a query. The demo page is available at `http://localhost:8000/demo/products`; the interface includes a control that switches its HTML structure to demonstrate selector recovery. The API documentation is available at `http://localhost:8000/docs`.

The frontend API client currently targets `http://localhost:8000`; the backend allows the Vite development origins on port 5173.

## Tests
l
Run the backend test script from the `backend` directory:

```powershell
python -X utf8 tests/test_pipeline.py
```

The tests cover query interpretation, extraction against the demo HTML, candidate generation and ranking, a cold-start pipeline run, recovery between the two demo structures, and multiple queries. The test script initializes and uses the local SQLite database.

## Results and Expected Outcomes

The included tests define expected behavior for the controlled demo: queries can extract fields from its product listings, and selectors saved for one HTML structure can be replaced after the demo switches to the other structure. These are test scenarios, not published performance measurements. Results on external websites depend on page accessibility and whether the page structure and target fields can be recognized by the implemented heuristics.

## Future Enhancements

- Evaluate selector-ranking approaches against a documented set of pages and structural changes.
- Expand automated tests to cover API authentication, batch uploads, and browser-loading behavior.
- Make the frontend API address and authentication secret configurable for deployment environments.
- Improve query interpretation and field recognition for page layouts beyond the controlled product demo.

## References

The current project files do not provide external academic references or datasets. Add the sources used for a research submission here.
