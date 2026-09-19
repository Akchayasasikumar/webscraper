export default function HistoryLog({ history = [] }) {
  return (
    <div className="panel" style={{ background: 'hsl(220,16%,9%)' }}>
      <div className="panel-header" style={{ background: 'hsl(220,16%,10%)' }}>
        <span className="panel-title">Healing History</span>
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
          {history.length} event{history.length !== 1 ? 's' : ''}
        </span>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🗄️</div>
          <div className="empty-state-text">No healing events yet.<br />History persists across sessions in SQLite.</div>
        </div>
      ) : (
        <div style={{ maxHeight: 340, overflowY: 'auto', padding: '4px 0' }}>
          {history.map(row => <HistoryRow key={row.id} row={row} />)}
        </div>
      )}
    </div>
  )
}

function HistoryRow({ row }) {
  const healed = row.final_status === 'healed'
  const ok     = row.final_status === 'ok'
  return (
    <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 6 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
          {fmtTime(row.timestamp)}
        </span>
        <span className={`badge ${healed ? 'badge-healed' : ok ? 'badge-ok' : 'badge-failed'}`}>
          {healed ? '✅ Healed' : ok ? '✓ OK' : '❌ Failed'}
        </span>
        {row.method === 'quantum'           && <span className="badge badge-quantum">⚛️ Quantum</span>}
        {row.method === 'classical_fallback' && <span className="badge badge-classical">📊 Classical</span>}
        <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>#{row.id}</span>
      </div>

      {/* Query */}
      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
        "{row.query}"
      </div>

      {/* Selector diff */}
      {(row.old_container_sel || row.new_container_sel) && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
          {row.old_container_sel && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <span className="sel-code" style={{ background: 'var(--alarm-dim)', borderColor: 'var(--alarm-border)', fontSize: '0.7rem' }}>
                {row.old_container_sel}
              </span>
              {row.old_field_sel && (
                <span className="sel-code" style={{ background: 'var(--alarm-dim)', borderColor: 'var(--alarm-border)', fontSize: '0.7rem' }}>
                  {row.old_field_sel}
                </span>
              )}
            </div>
          )}
          {row.new_container_sel && (
            <>
              <span style={{ color: 'var(--text-muted)', alignSelf: 'center' }}>→</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <span className="sel-code" style={{ background: 'var(--accent-dim)', borderColor: 'var(--accent-border)', color: 'var(--accent)', fontSize: '0.7rem' }}>
                  {row.new_container_sel}
                </span>
                {row.new_field_sel && (
                  <span className="sel-code" style={{ background: 'var(--accent-dim)', borderColor: 'var(--accent-border)', color: 'var(--accent)', fontSize: '0.7rem' }}>
                    {row.new_field_sel}
                  </span>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Results preview */}
      {row.result_items && row.result_items.length > 0 && (
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          → {row.result_items.slice(0, 4).join(', ')}{row.result_items.length > 4 ? ` +${row.result_items.length - 4} more` : ''}
        </div>
      )}
    </div>
  )
}

function fmtTime(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts + 'Z').toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    })
  } catch { return ts.slice(0, 19).replace('T', ' ') }
}
