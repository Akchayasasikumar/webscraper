import { batchDownloadUrl } from '../api'

export default function ResultsTable({ singleResult, batchResult }) {
  // Batch mode
  if (batchResult) {
    const { batch_id, results } = batchResult
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Batch Results</span>
          <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {results.length} quer{results.length !== 1 ? 'ies' : 'y'}
          </span>
          {batch_id && (
            <a
              id="btn-download-csv"
              href={batchDownloadUrl(batch_id)}
              download={`batch_${batch_id}.csv`}
              className="btn btn-ghost btn-sm"
              style={{ marginLeft: 8 }}
            >
              ⬇ Download CSV
            </a>
          )}
        </div>
        {results.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">📊</div><div className="empty-state-text">No results.</div></div>
        ) : (
          <div style={{ maxHeight: 380, overflowY: 'auto' }}>
            {results.map((r, i) => (
              <QueryResultSection key={i} result={r} idx={i} />
            ))}
          </div>
        )}
      </div>
    )
  }

  // Single mode
  if (singleResult) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Results</span>
          <StatusPill status={singleResult.final_status} />
        </div>
        <QueryResultSection result={singleResult} />
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="panel-header"><span className="panel-title">Results</span></div>
      <div className="empty-state">
        <div className="empty-state-icon">📊</div>
        <div className="empty-state-text">No results yet.<br />Enter a query above and click Run.</div>
      </div>
    </div>
  )
}

function QueryResultSection({ result, idx }) {
  const { query, interpreted, items, final_status } = result
  const field = interpreted?.field || ''
  const filter = interpreted?.filter_keyword || ''

  return (
    <div style={{ borderBottom: '1px solid var(--border-subtle)' }}>
      {/* Query header */}
      <div style={{ padding: '10px 16px', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        {idx !== undefined && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', minWidth: 20 }}>
            {idx + 1}.
          </span>
        )}
        <span style={{ fontSize: '0.82rem', fontStyle: 'italic', color: 'var(--text-secondary)' }}>"{query}"</span>
        <StatusPill status={final_status} />
        <span style={{ marginLeft: 'auto', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
          {items?.length || 0} item{items?.length !== 1 ? 's' : ''}
          {filter ? ` · filter: ${filter}` : ''}
          {field ? ` · field: ${field}` : ''}
        </span>
      </div>

      {/* Items */}
      {items && items.length > 0 ? (
        <div style={{ padding: '12px 16px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {items.map((v, i) => (
            <span key={i} className="result-chip" style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
              padding: '4px 10px', background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)',
              color: final_status === 'healed' || final_status === 'ok' ? 'var(--accent)' : 'var(--text-primary)',
            }}>
              {v}
            </span>
          ))}
        </div>
      ) : (
        <div style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '0.78rem', fontStyle: 'italic' }}>
          No items extracted — {result.failure_reason || 'unknown reason'}
        </div>
      )}
    </div>
  )
}

function StatusPill({ status }) {
  const map = {
    ok:               'badge-ok',
    healed:           'badge-healed',
    failed:           'badge-failed',
    no_candidates:    'badge-failed',
    validation_failed:'badge-failed',
  }
  return <span className={`badge ${map[status] || 'badge-idle'}`}>{status}</span>
}
