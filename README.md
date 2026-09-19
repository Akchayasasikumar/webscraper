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
| Frontend | React 18, Vite, Vanilla CSS |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Scraping | BeautifulSoup4, lxml, Playwright |
| Quantum | Qiskit, Qiskit-Aer (QAOA simulator) |
| LLM (optional) | Anthropic Claude API |
| Database | SQLite3 (built into Python) |

---

## 👩‍💻 Author

Built as a college project demonstrating AI, quantum computing, and web automation concepts.
