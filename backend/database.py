"""
database.py — SQLite schema and helpers.
Tables:
  healing_history  — one row per pipeline run (single query)
  selector_store   — persisted selectors per (url, query_hash)
  batch_results    — batch run storage for CSV download
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "scraper.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS healing_history (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT    NOT NULL,
            url                 TEXT    NOT NULL,
            query               TEXT    NOT NULL,
            field               TEXT,
            filter_keyword      TEXT,
            multiple            INTEGER,
            old_container_sel   TEXT,
            old_field_sel       TEXT,
            new_container_sel   TEXT,
            new_field_sel       TEXT,
            candidates_json     TEXT,
            scores_json         TEXT,
            method              TEXT,
            validation_ok       INTEGER,
            final_status        TEXT,
            failure_reason      TEXT,
            result_items_json   TEXT
        );

        CREATE TABLE IF NOT EXISTS selector_store (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            url                 TEXT    NOT NULL,
            query_hash          TEXT    NOT NULL,
            query               TEXT    NOT NULL,
            container_selector  TEXT    NOT NULL,
            field_selector      TEXT    NOT NULL,
            updated_at          TEXT    NOT NULL,
            UNIQUE(url, query_hash)
        );

        CREATE TABLE IF NOT EXISTS batch_results (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id            TEXT    NOT NULL,
            created_at          TEXT    NOT NULL,
            results_json        TEXT    NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── Selector store ────────────────────────────────────────────────────────────

def _query_hash(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]


def get_selectors(url: str, query: str) -> dict[str, str] | None:
    """Return stored selectors for (url, query) or None if not found."""
    conn = get_connection()
    row = conn.execute(
        "SELECT container_selector, field_selector FROM selector_store WHERE url=? AND query_hash=?",
        (url, _query_hash(query))
    ).fetchone()
    conn.close()
    if row:
        return {"container_selector": row["container_selector"],
                "field_selector":     row["field_selector"]}
    return None


def save_selectors(url: str, query: str, container_selector: str, field_selector: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO selector_store (url, query_hash, query, container_selector, field_selector, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(url, query_hash) DO UPDATE SET
               container_selector=excluded.container_selector,
               field_selector=excluded.field_selector,
               updated_at=excluded.updated_at""",
        (url, _query_hash(query), query, container_selector, field_selector,
         datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


# ── Healing history ───────────────────────────────────────────────────────────

def insert_history(
    url: str,
    query: str,
    interpreted: dict,
    old_selectors: dict,
    new_selectors: dict | None,
    candidates: list,
    scores: list,
    method: str,
    validation_ok: bool,
    final_status: str,
    failure_reason: str = "",
    result_items: list[str] | None = None,
) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO healing_history
           (timestamp, url, query, field, filter_keyword, multiple,
            old_container_sel, old_field_sel, new_container_sel, new_field_sel,
            candidates_json, scores_json, method, validation_ok, final_status,
            failure_reason, result_items_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.utcnow().isoformat(),
            url, query,
            interpreted.get("field"), interpreted.get("filter_keyword"),
            int(interpreted.get("multiple", True)),
            old_selectors.get("container_selector", ""),
            old_selectors.get("field_selector", ""),
            (new_selectors or {}).get("container_selector"),
            (new_selectors or {}).get("field_selector"),
            json.dumps(candidates),
            json.dumps(scores),
            method,
            int(validation_ok),
            final_status,
            failure_reason,
            json.dumps(result_items or []),
        )
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def get_history(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM healing_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["candidates"] = json.loads(d.pop("candidates_json", "[]") or "[]")
        d["scores"]     = json.loads(d.pop("scores_json", "[]") or "[]")
        d["result_items"] = json.loads(d.pop("result_items_json", "[]") or "[]")
        result.append(d)
    return result


# ── Batch results ─────────────────────────────────────────────────────────────

def save_batch(batch_id: str, results: list[dict]) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO batch_results (batch_id, created_at, results_json) VALUES (?,?,?)",
        (batch_id, datetime.utcnow().isoformat(), json.dumps(results))
    )
    conn.commit()
    conn.close()


def get_batch(batch_id: str) -> list[dict] | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT results_json FROM batch_results WHERE batch_id=?", (batch_id,)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row["results_json"])
    return None
