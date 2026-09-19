import { useState } from 'react'
import './QueryInput.css'

const DEMO_URL = 'http://localhost:8000/demo/products'

const EXAMPLE_QUERIES = [
  'retrieve all the lipstick prices',
  'get every product name on the page',
  'show me foundation ratings',
  'find all serum prices',
]

export default function QueryInput({ onQuery, onBatch, loading, disabled }) {
  return (
    <div className="qi-panel panel">
      <div className="panel-header">
        <span className="panel-title">Query Input</span>
        <span style={{ marginLeft: 'auto', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
          No CSS selectors needed — the system figures it out
        </span>
      </div>
      <div className="panel-body">
        <QueryTabs onQuery={onQuery} onBatch={onBatch} loading={loading} disabled={disabled} />
      </div>
    </div>
  )
}

function QueryTabs({ onQuery, onBatch, loading, disabled }) {
  const [mode, setMode]       = useState('text')
  const [url, setUrl]         = useState(DEMO_URL)
  const [query, setQuery]     = useState('')
  const [file, setFile]       = useState(null)
  const [dragOver, setDragOver] = useState(false)

  function handleRun() {
    if (mode === 'text') {
      if (!query.trim()) return
      onQuery(url.trim(), query.trim())
    } else {
      if (!file) return
      onBatch(url.trim(), file)
    }
  }

  const canRun = !loading && !disabled && (mode === 'text' ? query.trim() : !!file)

  return (
    <div className="qi-body">
      {/* URL field */}
      <div className="qi-field">
        <label className="field-label" htmlFor="qi-url">Target URL</label>
        <input
          id="qi-url"
          className="field-input"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://example.com/products"
        />
      </div>

      {/* Mode toggle */}
      <div className="qi-mode-toggle">
        <button
          id="qi-mode-text"
          className={`qi-tab ${mode === 'text' ? 'qi-tab--active' : ''}`}
          onClick={() => setMode('text')}
        >
          ✏️ Type a query
        </button>
        <button
          id="qi-mode-file"
          className={`qi-tab ${mode === 'file' ? 'qi-tab--active' : ''}`}
          onClick={() => setMode('file')}
        >
          📄 Upload batch file
        </button>
      </div>

      {/* Text mode */}
      {mode === 'text' && (
        <div className="qi-text-mode">
          <div className="qi-field">
            <label className="field-label" htmlFor="qi-query">Natural Language Query</label>
            <input
              id="qi-query"
              className="field-input"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && canRun && handleRun()}
              placeholder="e.g. retrieve all the lipstick prices"
            />
          </div>
          <div className="qi-examples">
            <span className="field-label">Examples:</span>
            {EXAMPLE_QUERIES.map(q => (
              <button
                key={q}
                className="qi-example-chip"
                onClick={() => setQuery(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* File mode */}
      {mode === 'file' && (
        <div className="qi-file-mode">
          <div
            className={`qi-dropzone ${dragOver ? 'qi-dropzone--over' : ''} ${file ? 'qi-dropzone--has-file' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => {
              e.preventDefault(); setDragOver(false)
              const f = e.dataTransfer.files[0]
              if (f) setFile(f)
            }}
          >
            <input
              id="qi-file"
              type="file"
              accept=".txt,.csv"
              style={{ display: 'none' }}
              onChange={e => setFile(e.target.files[0] || null)}
            />
            {file ? (
              <div className="qi-file-info">
                <span style={{ fontSize: '1.5rem' }}>📄</span>
                <div>
                  <div style={{ fontWeight: 600 }}>{file.name}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {(file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => setFile(null)}>✕ Remove</button>
              </div>
            ) : (
              <div className="qi-dropzone-empty">
                <span style={{ fontSize: '2rem', opacity: 0.4 }}>📂</span>
                <div style={{ fontSize: '0.82rem' }}>
                  Drop a .txt file here, or{' '}
                  <label htmlFor="qi-file" style={{ color: 'var(--accent)', cursor: 'pointer', textDecoration: 'underline' }}>
                    browse
                  </label>
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  One query per line, e.g.: retrieve all the lipstick prices
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Run button */}
      <div className="qi-actions">
        <button
          id="btn-run"
          className="btn btn-primary"
          onClick={handleRun}
          disabled={!canRun}
        >
          {loading ? '⏳ Running…' : mode === 'text' ? '▶ Run Query' : '▶ Run Batch'}
        </button>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {mode === 'file' && 'Results and CSV download appear in the table below'}
        </span>
      </div>
    </div>
  )
}
