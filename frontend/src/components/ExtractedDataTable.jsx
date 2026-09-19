export default function ExtractedDataTable({ scrapeLog = [], currentSelector, lastValue, status }) {
  const isEmpty = !scrapeLog || scrapeLog.length === 0

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Extracted Data</span>
        {currentSelector && (
          <span className="selector-code" style={{ marginLeft: 'auto', fontSize: '0.72rem', padding: '3px 8px' }}>
            {currentSelector}
          </span>
        )}
      </div>

      {/* Live value */}
      {lastValue && (
        <div style={{
          padding: '10px 18px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', fontWeight: 600 }}>
            Latest
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '1.1rem',
            fontWeight: 600,
            color: status === 'scraping' ? 'var(--accent)' : 'var(--text-primary)',
          }}>
            {lastValue}
          </span>
          {status === 'scraping' && (
            <span className="dot-pulse dot-scraping" style={{ marginLeft: 4 }} />
          )}
        </div>
      )}

      {isEmpty ? (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-text">No data extracted yet.<br />Start scraping to see values here.</div>
        </div>
      ) : (
        <div style={{ maxHeight: 240, overflowY: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Selector</th>
                <th>Value</th>
                <th style={{ width: 70, textAlign: 'center' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {scrapeLog.slice(0, 30).map(row => (
                <tr key={row.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {formatTime(row.timestamp)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.selector}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: row.value ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {row.value || '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <StatusDot status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatusDot({ status }) {
  if (status === 'ok')     return <span style={{ color: 'var(--accent)', fontWeight: 700 }}>✓</span>
  if (status === 'failed') return <span style={{ color: 'var(--alarm)', fontWeight: 700 }}>✗</span>
  if (status === 'healed') return <span style={{ color: 'var(--warn)', fontWeight: 700 }}>⚡</span>
  return <span style={{ color: 'var(--text-muted)' }}>—</span>
}

function formatTime(ts) {
  if (!ts) return '—'
  try {
    const d = new Date(ts + 'Z')
    return d.toLocaleTimeString(undefined, { hour12: false })
  } catch {
    return ts.slice(11, 19)
  }
}
