"""
main.py — FastAPI application for the Self-Healing Scraper.

Endpoints:
  POST  /scraper/query                — single text query → results
  POST  /scraper/batch                — upload file of queries → batch results
  GET   /scraper/batch/{batch_id}/download — CSV download
  GET   /scraper/status               — current pipeline state (polled by frontend)
  POST  /demo/simulate-change         — toggle demo site structure
  GET   /demo/products                — current demo page HTML
  GET   /demo/structure               — current structure name
  GET   /scraper/history              — full healing history
  GET   /health                       — liveness check
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

import demo_site
from browser import get_rendered_html, BrowserFetchError
from database import get_batch, get_history, init_db, save_batch
from pipeline import run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Shared state ──────────────────────────────────────────────────────────────
_state: dict[str, Any] = {
    "status":             "idle",
    "pipeline_step":      "",
    "pipeline_steps_done": [],
    "current_query":      "",
    "interpreted":        {},
    "last_items":         [],
    "new_selectors":      None,
    "demo_structure":     "A",
    "error":              None,
    "last_result":        None,
}


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Database initialised.")
    yield


app = FastAPI(title="Self-Healing Scraper API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reset_state():
    _state.update({
        "status": "idle",
        "pipeline_step": "",
        "pipeline_steps_done": [],
        "current_query": "",
        "interpreted": {},
        "last_items": [],
        "new_selectors": None,
        "error": None,
        "last_result": None,
        "demo_structure": demo_site.get_current_structure(),
    })


# ── Request models ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    url:   str = "http://localhost:8000/demo/products"
    query: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/scraper/query")
async def scraper_query(req: QueryRequest):
    """Run the pipeline for a single text query."""
    _reset_state()
    _state["status"] = "loading"
    _state["pipeline_step"] = "LOADING_PAGE"
    _state["current_query"] = req.query
    _state["demo_structure"] = demo_site.get_current_structure()

    # ── Fetch / render the page (Playwright for external URLs) ────────────────
    loop = asyncio.get_event_loop()
    try:
        html = await loop.run_in_executor(
            None,
            lambda: get_rendered_html(req.url),
        )
    except BrowserFetchError as exc:
        _state["status"] = "failed"
        _state["error"] = str(exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        _state["status"] = "failed"
        _state["error"] = str(exc)
        raise HTTPException(status_code=502, detail=f"Could not load page: {exc}")

    # ── Run healing pipeline in a thread ─────────────────────────────────────
    _state["status"] = "scraping"
    result = await loop.run_in_executor(
        None,
        lambda: run_query(req.url, req.query, html, _state),
    )

    _state["last_result"]     = result
    _state["demo_structure"]  = demo_site.get_current_structure()
    return result


@app.post("/scraper/batch")
async def scraper_batch(
    url:  str = Form(default="http://localhost:8000/demo/products"),
    file: UploadFile = File(...),
):
    """
    Accept an uploaded plain-text file with one query per line.
    Runs the pipeline for each non-empty line.
    Returns a batch_id for CSV download + the per-query results array.
    """
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {exc}")

    queries = [line.strip() for line in text.splitlines() if line.strip()]
    if not queries:
        raise HTTPException(status_code=400, detail="Uploaded file contains no queries.")

    loop = asyncio.get_event_loop()
    try:
        html = await loop.run_in_executor(
            None,
            lambda: get_rendered_html(url),
        )
    except BrowserFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load page: {exc}")

    batch_id = str(uuid.uuid4())[:8]
    results  = []
    loop     = asyncio.get_event_loop()

    for q in queries:
        # Each query gets a fresh state snapshot for status, but we reuse html
        q_state: dict[str, Any] = {
            "status": "idle", "pipeline_step": "", "pipeline_steps_done": [],
            "current_query": q, "interpreted": {}, "last_items": [],
            "new_selectors": None, "error": None,
        }
        # Update shared state so /scraper/status reflects current query
        _state.update({
            "status": "scraping",
            "current_query": q,
            "pipeline_step": "",
            "pipeline_steps_done": [],
            "demo_structure": demo_site.get_current_structure(),
        })
        r = await loop.run_in_executor(
            None, lambda _q=q, _s=q_state: run_query(url, _q, html, _s)
        )
        results.append(r)

    # Persist for CSV download
    save_batch(batch_id, results)
    _state["status"] = "idle"
    _state["last_result"] = {"batch_id": batch_id, "results": results}

    return {"batch_id": batch_id, "results": results}


@app.get("/scraper/batch/{batch_id}/download")
async def batch_download(batch_id: str):
    """Return batch results as a downloadable CSV."""
    results = get_batch(batch_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Batch not found.")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["query", "field", "filter_keyword", "item_index", "value", "status"])
    for r in results:
        interp = r.get("interpreted", {})
        q      = r.get("query", "")
        field  = interp.get("field", "")
        fk     = interp.get("filter_keyword", "")
        status = r.get("final_status", "")
        items  = r.get("items", [])
        if items:
            for idx, val in enumerate(items, 1):
                writer.writerow([q, field, fk, idx, val, status])
        else:
            writer.writerow([q, field, fk, 0, "", status])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.csv"},
    )


@app.get("/scraper/status")
async def scraper_status():
    return {**_state, "demo_structure": demo_site.get_current_structure()}


@app.get("/scraper/history")
async def scraper_history(limit: int = 50):
    return get_history(limit)


@app.post("/demo/simulate-change")
async def simulate_change():
    new = demo_site.toggle_structure()
    _state["demo_structure"] = new
    logger.info("Demo structure toggled → %s", new)
    return {"structure": new, "message": f"Demo site switched to structure {new}"}


@app.get("/demo/products", response_class=HTMLResponse)
async def demo_products():
    return HTMLResponse(content=demo_site.get_demo_html())


@app.get("/demo/structure")
async def demo_structure_info():
    return {"structure": demo_site.get_current_structure()}


@app.post("/demo/toggle")
async def demo_toggle():
    """Alias used during Phase 1 verification."""
    return await simulate_change()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
