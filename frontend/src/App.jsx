import { useState, useEffect, useCallback, useRef } from 'react'
import QueryInput from './components/QueryInput'
import PipelineFlow from './components/PipelineFlow'
import SelectorComparison from './components/SelectorComparison'
import CandidateList from './components/CandidateList'
import ResultsTable from './components/ResultsTable'
import HistoryLog from './components/HistoryLog'
import { runQuery, runBatch, getStatus, simulateChange, getHistory, checkHealth } from './api'

export default function App() {
  const [polledStatus, setPolledStatus] = useState(null)
  const [history, setHistory]           = useState([])
  const [singleResult, setSingleResult] = useState(null)
  const [batchResult, setBatchResult]   = useState(null)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState(null)
  const [simulating, setSimulating]     = useState(false)
  const [backendOk, setBackendOk]       = useState(null)
  const pollRef = useRef(null)

  // Health check
  useEffect(() => { checkHealth().then(ok => setBackendOk(ok)) }, [])

  // Poll /scraper/status + history every 1s
  const poll = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([getStatus(), getHistory()])
      setPolledStatus(s)
      setHistory(h)
      if (error === 'Cannot reach backend — is the server running?') setError(null)
    } catch {
      setError('Cannot reach backend — is the server running?')
      setBackendOk(false)
    }
  }, [error])

  useEffect(() => {
    poll()
    pollRef.current = setInterval(poll, 1000)
    return () => clearInterval(pollRef.current)
  }, [poll])

  // ── Handlers ──────────────────────────────────────────────────────────────
  async function handleQuery(url, query) {
    setLoading(true)
    setError(null)
    setSingleResult(null)
    setBatchResult(null)
    try {
      const result = await runQuery(url, query)
      setSingleResult(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleBatch(url, file) {
    setLoading(true)
    setError(null)
    setSingleResult(null)
    setBatchResult(null)
    try {
      const result = await runBatch(url, file)
      setBatchResult(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSimulate() {
    if (simulating) return
    setSimulating(true)
    setError(null)
    try {
      await simulateChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setTimeout(() => setSimulating(false), 1500)
    }
  }

  // Derive display state
  const scraperStatus = polledStatus?.status || 'idle'
  const pipelineStep  = polledStatus?.pipeline_step || ''
  const stepsDone     = polledStatus?.pipeline_steps_done || []
  const demoStructure = polledStatus?.demo_structure || 'A'

  // The "last result" for SelectorComparison/CandidateList comes from
  // the most recent query result (stored locally), not polled status
  const displayResult = singleResult || (batchResult?.results?.[batchResult.results.length - 1])

  return (
    <div>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">🕷️</div>
          <div>
            <div className="app-logo-name">Self-Healing Scraper</div>
            <div className="app-logo-sub">AI · Quantum-Assisted · Zero Manual Selectors</div>
          </div>
        </div>

        <div className="app-header-right">
          {backendOk === false && (
            <span className="badge badge-failed">⚠ Backend offline</span>
          )}

          {/* Demo structure indicator */}
          <div className="struct-badge">
            <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>STRUCTURE</span>
            <span style={{ fontWeight: 700, color: demoStructure === 'A' ? 'var(--info)' : 'var(--warn)' }}>
              {demoStructure}
            </span>
          </div>

          {/* Status badge */}
          <StatusBadge status={loading ? 'scraping' : scraperStatus} />

          {/* Simulate Website Change */}
          <button
            id="btn-simulate-change"
            className="btn btn-danger"
            onClick={handleSimulate}
            disabled={simulating}
            title="Toggle the demo site HTML structure (A ↔ B), which will break the current selector and trigger healing"
          >
            {simulating ? '⏳' : '💥'} Simulate Website Change
          </button>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="app-main">

        {/* Backend error */}
        {error && (
          <div className="error-banner">
            <span style={{ flexShrink: 0 }}>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Query Input */}
        <QueryInput
          onQuery={handleQuery}
          onBatch={handleBatch}
          loading={loading}
          disabled={false}
        />

        {/* Pipeline Flow (full width) */}
        <PipelineFlow
          pipelineStep={pipelineStep}
          stepsDone={stepsDone}
        />

        {/* Selector Comparison + Candidate List */}
        <div className="grid-2">
          <SelectorComparison lastResult={displayResult} status={scraperStatus} />
          <CandidateList lastResult={displayResult} />
        </div>

        {/* Results + History */}
        <div className="grid-2">
          <ResultsTable singleResult={singleResult} batchResult={batchResult} />
          <HistoryLog history={history} />
        </div>

      </main>
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    idle:     { cls: 'badge-idle',     dot: 'dot-idle',     label: 'Idle' },
    scraping: { cls: 'badge-scraping', dot: 'dot-scraping', label: 'Active' },
    healing:  { cls: 'badge-healing',  dot: 'dot-healing',  label: 'Healing' },
    failed:   { cls: 'badge-failed',   dot: 'dot-failed',   label: 'Failed' },
    stopped:  { cls: 'badge-idle',     dot: 'dot-idle',     label: 'Stopped' },
  }
  const m = map[status] || map.idle
  return (
    <span className={`badge ${m.cls}`}>
      <span className={`dot-pulse ${m.dot}`} />
      {m.label}
    </span>
  )
}
