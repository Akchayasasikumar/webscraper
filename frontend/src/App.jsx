import { useState, useEffect, useCallback, useRef } from 'react'
import QueryInput from './components/QueryInput'
import PipelineFlow from './components/PipelineFlow'
import SelectorComparison from './components/SelectorComparison'
import CandidateList from './components/CandidateList'
import ResultsTable from './components/ResultsTable'
import HistoryLog from './components/HistoryLog'
import { runQuery, runBatch, getStatus, simulateChange, getHistory, checkHealth, getCurrentUser, login, signup } from './api'

export default function App() {
  const [authUser, setAuthUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [authBusy, setAuthBusy] = useState(false)
  const [authError, setAuthError] = useState(null)
  const [activePage, setActivePage] = useState('overview')
  const [polledStatus, setPolledStatus] = useState(null)
  const [history, setHistory]           = useState([])
  const [singleResult, setSingleResult] = useState(null)
  const [batchResult, setBatchResult]   = useState(null)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState(null)
  const [simulating, setSimulating]     = useState(false)
  const [backendOk, setBackendOk]       = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    if (!localStorage.getItem('scraper_token')) {
      setAuthChecked(true)
      return
    }
    getCurrentUser()
      .then(setAuthUser)
      .catch(() => localStorage.removeItem('scraper_token'))
      .finally(() => setAuthChecked(true))
  }, [])

  // Health check
  useEffect(() => { checkHealth().then(ok => setBackendOk(ok)) }, [])

  // Poll /scraper/status + history every 1s
  const poll = useCallback(async () => {
    if (!authUser) return
    try {
      const [s, h] = await Promise.all([getStatus(), getHistory()])
      setPolledStatus(s)
      setHistory(h)
      if (error === 'Cannot reach backend — is the server running?') setError(null)
    } catch {
      setError('Cannot reach backend — is the server running?')
      setBackendOk(false)
    }
  }, [authUser, error])

  useEffect(() => {
    if (!authUser) return undefined
    poll()
    pollRef.current = setInterval(poll, 1000)
    return () => clearInterval(pollRef.current)
  }, [authUser, poll])

  async function handleAuth(mode, email, password) {
    setAuthBusy(true)
    setAuthError(null)
    try {
      const result = mode === 'signup' ? await signup(email, password) : await login(email, password)
      localStorage.setItem('scraper_token', result.token)
      setAuthUser(result.user)
    } catch (e) {
      setAuthError(e.message)
    } finally {
      setAuthBusy(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('scraper_token')
    setAuthUser(null)
    setPolledStatus(null)
    setSingleResult(null)
    setBatchResult(null)
  }

  if (!authChecked) return <div className="auth-loading">Loading workspace…</div>
  if (!authUser) return <AuthScreen onSubmit={handleAuth} loading={authBusy} error={authError} />

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

  const currentStatus = loading ? 'scraping' : scraperStatus
  const pageMeta = {
    overview: { eyebrow: 'Workspace overview', title: 'Self-healing scraping, at a glance', description: 'Monitor extraction jobs, repair selectors, and review the latest activity.' },
    scrape: { eyebrow: 'New scrape', title: 'Start a scraping job', description: 'Describe the data you need in plain language. The system handles selectors for you.' },
    pipeline: { eyebrow: 'Live pipeline', title: 'Watch the repair process', description: 'Follow every stage as the scraper loads, detects, heals, validates, and resumes.' },
    results: { eyebrow: 'Extracted data', title: 'Review your results', description: 'Inspect extracted values and download completed batch jobs.' },
    insights: { eyebrow: 'Healing insights', title: 'Understand selector repairs', description: 'Compare broken selectors with their validated replacements and ranked candidates.' },
    history: { eyebrow: 'Activity history', title: 'Healing history', description: 'Review the repair events retained by the scraper database.' },
  }

  function openPage(page) {
    setActivePage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">✦</div>
          <div>
            <div className="brand-name">Self-Healing</div>
            <div className="brand-caption">SCRAPER CONTROL</div>
          </div>
        </div>

        <div className="sidebar-section-label">Workspace</div>
        <nav className="primary-nav" aria-label="Primary navigation">
          <NavItem icon="⌂" label="Overview" page="overview" activePage={activePage} onClick={openPage} />
          <NavItem icon="＋" label="New scrape" page="scrape" activePage={activePage} onClick={openPage} />
          <NavItem icon="◌" label="Live pipeline" page="pipeline" activePage={activePage} onClick={openPage} />
          <NavItem icon="▤" label="Results" page="results" activePage={activePage} onClick={openPage} />
          <NavItem icon="◇" label="Healing insights" page="insights" activePage={activePage} onClick={openPage} />
          <NavItem icon="◷" label="History" page="history" activePage={activePage} onClick={openPage} />
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-footer-label">System mode</div>
          <div className="sidebar-footer-value"><span className="status-dot status-dot--live" /> Automatic healing enabled</div>
        </div>
      </aside>

      <div className="app-workspace">
        <header className="app-header">
          <div className="mobile-brand"><span className="brand-mark">✦</span><span>Self-Healing</span></div>
          <div className="header-context">{pageMeta[activePage].eyebrow}</div>
          <div className="app-header-right">
            <div className={`connection-state ${backendOk === false ? 'connection-state--offline' : ''}`}>
              <span className={`status-dot ${backendOk === false ? 'status-dot--offline' : 'status-dot--live'}`} />
              {backendOk === false ? 'Backend offline' : 'Backend connected'}
            </div>
            <div className="struct-badge"><span>STRUCTURE</span><strong className={demoStructure === 'A' ? 'structure-a' : 'structure-b'}>{demoStructure}</strong></div>
            <StatusBadge status={currentStatus} />
            <button className="account-button" onClick={handleLogout} title={`Sign out ${authUser.email}`}>Sign out</button>
          </div>
        </header>

        <main className="app-main">
          <div className="page-heading">
            <div>
              <div className="eyebrow">{pageMeta[activePage].eyebrow}</div>
              <h1>{pageMeta[activePage].title}</h1>
              <p>{pageMeta[activePage].description}</p>
            </div>
            <button
              id="btn-simulate-change"
              className="btn btn-danger"
              onClick={handleSimulate}
              disabled={simulating}
              title="Toggle the demo site HTML structure, which will break the current selector and trigger healing"
            >
              {simulating ? '⏳ Simulating…' : '💥 Simulate change'}
            </button>
          </div>

          {error && <div className="error-banner"><span>⚠</span><span>{error}</span></div>}

          {activePage === 'overview' && (
            <OverviewPage
              backendOk={backendOk}
              currentStatus={currentStatus}
              demoStructure={demoStructure}
              history={history}
              displayResult={displayResult}
              pipelineStep={pipelineStep}
              stepsDone={stepsDone}
              onOpenPage={openPage}
            />
          )}
          {activePage === 'scrape' && <QueryInput onQuery={handleQuery} onBatch={handleBatch} loading={loading} disabled={false} />}
          {activePage === 'pipeline' && <PipelineFlow pipelineStep={pipelineStep} stepsDone={stepsDone} />}
          {activePage === 'results' && <ResultsTable singleResult={singleResult} batchResult={batchResult} />}
          {activePage === 'insights' && <div className="grid-2"><SelectorComparison lastResult={displayResult} status={scraperStatus} /><CandidateList lastResult={displayResult} /></div>}
          {activePage === 'history' && <HistoryLog history={history} />}
        </main>
      </div>
    </div>
  )
}

function NavItem({ icon, label, page, activePage, onClick }) {
  return <button className={`nav-item ${activePage === page ? 'nav-item--active' : ''}`} onClick={() => onClick(page)}><span className="nav-icon">{icon}</span><span>{label}</span></button>
}

function OverviewPage({ backendOk, currentStatus, demoStructure, history, displayResult, pipelineStep, stepsDone, onOpenPage }) {
  const latestItems = displayResult?.items || []
  return (
    <div className="overview-page">
      <section className="overview-hero">
        <div>
          <span className="hero-kicker">AUTOMATION THAT ADAPTS</span>
          <h2>Scrape confidently.<br /><em>Recover automatically.</em></h2>
          <p>Ask for the data you need. When websites change, your selectors change with them.</p>
        </div>
        <button className="btn btn-primary btn-large" onClick={() => onOpenPage('scrape')}>＋ Start a new scrape</button>
      </section>

      <section className="metric-grid" aria-label="Workspace metrics">
        <MetricCard label="Backend" value={backendOk === false ? 'Offline' : 'Connected'} detail="FastAPI service" tone={backendOk === false ? 'alarm' : 'success'} />
        <MetricCard label="Scraper status" value={currentStatus} detail="Live pipeline state" tone={currentStatus === 'healing' ? 'warning' : 'info'} />
        <MetricCard label="Demo structure" value={`Variant ${demoStructure}`} detail="Current HTML shape" tone="neutral" />
        <MetricCard label="Healing events" value={history.length} detail="Persisted in SQLite" tone="success" />
      </section>

      <div className="overview-grid">
        <section className="dashboard-section dashboard-section--pipeline">
          <div className="section-heading"><div><span className="section-kicker">LIVE MONITOR</span><h3>Pipeline activity</h3></div><button className="text-button" onClick={() => onOpenPage('pipeline')}>Open full view →</button></div>
          <PipelineFlow pipelineStep={pipelineStep} stepsDone={stepsDone} />
        </section>
        <section className="dashboard-section recent-card">
          <div className="section-heading"><div><span className="section-kicker">LATEST OUTPUT</span><h3>Recent extraction</h3></div><button className="text-button" onClick={() => onOpenPage('results')}>View results →</button></div>
          {displayResult ? <><div className="recent-query">“{displayResult.query}”</div><div className="recent-result-value">{latestItems.length} <span>items extracted</span></div><div className="result-preview">{latestItems.slice(0, 4).map((item, index) => <span key={index}>{item}</span>)}</div></> : <div className="overview-empty">Run a query to see extracted values here.</div>}
        </section>
      </div>

      <section className="dashboard-section activity-card">
        <div className="section-heading"><div><span className="section-kicker">SYSTEM ACTIVITY</span><h3>Healing history</h3></div><button className="text-button" onClick={() => onOpenPage('history')}>View history →</button></div>
        {history.length ? <div className="activity-list">{history.slice(0, 3).map(row => <div className="activity-row" key={row.id}><span className="activity-marker" /><div><strong>{row.final_status === 'healed' ? 'Selector repaired' : 'Scrape completed'}</strong><span>{row.query}</span></div><time>{formatOverviewTime(row.timestamp)}</time></div>)}</div> : <div className="overview-empty">No healing events have been recorded yet.</div>}
      </section>
    </div>
  )
}

function MetricCard({ label, value, detail, tone }) {
  return <div className="metric-card"><div className={`metric-icon metric-icon--${tone}`}>◆</div><div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div></div>
}

function formatOverviewTime(timestamp) {
  if (!timestamp) return '—'
  try { return new Date(`${timestamp}Z`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } catch { return '—' }
}

function AuthScreen({ onSubmit, loading, error }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function submit(event) {
    event.preventDefault()
    onSubmit(mode, email.trim(), password)
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div className="auth-brand"><span className="brand-mark">✦</span><div><strong>Self-Healing</strong><small>SCRAPER CONTROL</small></div></div>
        <div className="auth-copy"><span className="eyebrow">Private workspace</span><h1>{mode === 'login' ? 'Welcome back.' : 'Create your workspace.'}</h1><p>{mode === 'login' ? 'Sign in to monitor resilient scraping jobs.' : 'Create an account to start managing your scraping jobs.'}</p></div>
        <form className="auth-form" onSubmit={submit}>
          <label className="field-label" htmlFor="auth-email">Email address</label>
          <input id="auth-email" className="field-input" type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required />
          <label className="field-label" htmlFor="auth-password">Password</label>
          <input id="auth-password" className="field-input" type="password" value={password} onChange={event => setPassword(event.target.value)} placeholder="At least 8 characters" minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required />
          {error && <div className="auth-error">{error}</div>}
          <button className="btn btn-primary auth-submit" disabled={loading}>{loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
        </form>
        <button className="auth-switch" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
          {mode === 'login' ? 'Need an account? Create one' : 'Already have an account? Sign in'}
        </button>
      </section>
      <section className="auth-aside"><span className="hero-kicker">AUTOMATION THAT ADAPTS</span><h2>Scrape confidently.<br /><em>Recover automatically.</em></h2><p>One workspace for resilient extraction, live pipeline monitoring, and selector repair.</p></section>
    </main>
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
