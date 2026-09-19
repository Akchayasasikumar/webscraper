export default function CandidateList({ lastResult }) {
  const ranked = lastResult?.ranked || []
  const validation = lastResult?.validation || []
  const method = lastResult?.method
  const source = lastResult?.candidate_source

  // Build validation map
  const validMap = {}
  validation.forEach(v => {
    const key = `${v.candidate?.container_selector}||${v.candidate?.field_selector}`
    validMap[key] = v
  })

  if (!ranked.length) return (
    <div className="panel">
      <div className="panel-header"><span className="panel-title">Candidate Selectors</span></div>
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <div className="empty-state-text">No candidates yet.<br />Trigger a website change to see candidates appear here.</div>
      </div>
    </div>
  )

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Candidate Selectors</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          {source === 'llm'      && <span className="badge" style={{ background: 'hsla(270,80%,60%,0.10)', color: 'hsl(270,80%,78%)', border: '1px solid hsla(270,80%,60%,0.25)' }}>🤖 LLM</span>}
          {source === 'heuristic'&& <span className="badge badge-idle">🔍 Heuristic</span>}
          {method === 'quantum'          && <span className="badge badge-quantum">⚛️ Quantum</span>}
          {method === 'classical_fallback'&& <span className="badge badge-classical">📊 Classical</span>}
        </div>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 28 }}>#</th>
              <th>Container</th>
              <th>Field</th>
              <th style={{ width: 72, textAlign: 'right' }}>Score</th>
              <th style={{ width: 60, textAlign: 'center' }}>Valid</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((entry, idx) => {
              const cand = entry.candidate
              const key  = `${cand?.container_selector}||${cand?.field_selector}`
              const vr   = validMap[key]
              const isTop = idx === 0
              return (
                <tr key={key} style={isTop ? { background: 'var(--accent-dim)' } : {}}>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                    {idx + 1}
                  </td>
                  <td>
                    <span className="sel-code" style={{
                      background: 'transparent', border: 'none', padding: 0,
                      color: isTop ? 'var(--accent)' : 'var(--text-primary)',
                    }}>
                      {cand?.container_selector}
                    </span>
                    {isTop && <span style={{ marginLeft: 6, fontSize: '0.6rem', color: 'var(--accent)', fontWeight: 700 }}>BEST</span>}
                  </td>
                  <td>
                    <span className="sel-code" style={{ background: 'transparent', border: 'none', padding: 0, color: 'var(--text-secondary)' }}>
                      {cand?.field_selector}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <ScoreBar score={entry.score} />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {vr?.valid === true  && <span style={{ color: 'var(--accent)', fontWeight: 700 }}>✅</span>}
                    {vr?.valid === false && <span style={{ color: 'var(--alarm)', fontWeight: 700 }}>❌</span>}
                    {vr == null          && <span style={{ color: 'var(--text-muted)' }}>—</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ScoreBar({ score }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct > 65 ? 'var(--accent)' : pct > 35 ? 'var(--warn)' : 'var(--alarm)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>
      <div style={{ width: 44, height: 3, background: 'var(--bg-base)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, transition: 'width 600ms ease' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-secondary)', minWidth: 30, textAlign: 'right' }}>
        {score != null ? score.toFixed(2) : '—'}
      </span>
    </div>
  )
}
