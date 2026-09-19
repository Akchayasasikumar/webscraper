// api.js — Fetch wrappers for all backend endpoints

const BASE = 'http://localhost:8000'

export async function runQuery(url, query) {
  const res = await fetch(`${BASE}/scraper/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, query }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export async function runBatch(url, file) {
  const form = new FormData()
  form.append('url', url)
  form.append('file', file)
  const res = await fetch(`${BASE}/scraper/batch`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export function batchDownloadUrl(batchId) {
  return `${BASE}/scraper/batch/${batchId}/download`
}

export async function getStatus() {
  const res = await fetch(`${BASE}/scraper/status`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

export async function simulateChange() {
  const res = await fetch(`${BASE}/demo/simulate-change`, { method: 'POST' })
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

export async function getHistory() {
  const res = await fetch(`${BASE}/scraper/history`)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(2000) })
    return res.ok
  } catch { return false }
}
