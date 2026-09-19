import './SelectorComparison.css'

export default function SelectorComparison({ lastResult, status }) {
  if (!lastResult) return null
  const { old_selectors, new_selectors, interpreted, failure_reason } = lastResult
  const healed = lastResult.final_status === 'healed'
  const failed = lastResult.final_status === 'validation_failed' || lastResult.final_status === 'no_candidates'
  const showAlarm = healed || failed || failure_reason

  return (
    <div className={`panel sc-panel ${showAlarm && !healed ? 'sc-panel--alarm' : ''} ${healed ? 'sc-panel--healed' : ''}`}>
      <div className="panel-header">
        <span className="panel-title">Selector Comparison</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          {healed && <span className="badge badge-healed">✅ Repaired</span>}
          {failed && <span className="badge badge-failed">❌ Healing Failed</span>}
          {!healed && !failed && failure_reason && <span className="badge badge-healing">⚡ Healing</span>}
        </div>
      </div>
      <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

        {/* Interpreted query */}
        {interpreted && (
          <div className="sc-row">
            <span className="field-label">Interpreted</span>
            <div className="sc-interp">
              <Tag label="field" value={interpreted.field} />
              {interpreted.filter_keyword && <Tag label="filter" value={interpreted.filter_keyword} />}
              <Tag label="multiple" value={String(interpreted.multiple)} />
              {interpreted.source && <Tag label="source" value={interpreted.source} accent />}
            </div>
          </div>
        )}

        {/* Old selectors */}
        {(old_selectors?.container_selector || old_selectors?.field_selector) && (
          <div className="sc-row">
            <div className="sc-label-row">
              <span className="field-label">Old Selectors</span>
              {showAlarm && <span className="badge badge-failed">❌ Failed</span>}
            </div>
            <div className="sc-selector-pair sc-selector-pair--old">
              <SelectorPill label="container" value={old_selectors.container_selector} />
              <SelectorPill label="field" value={old_selectors.field_selector} />
            </div>
          </div>
        )}

        {/* Divider */}
        {(old_selectors?.container_selector || new_selectors) && (
          <div className="sc-arrow">
            <div className="sc-arrow-line" />
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              {healed ? '→' : '⚡'}
            </span>
            <div className="sc-arrow-line" />
          </div>
        )}

        {/* New selectors */}
        <div className="sc-row">
          <div className="sc-label-row">
            <span className="field-label">New Selectors</span>
            {healed && <span className="badge badge-healed">✅ Validated</span>}
          </div>
          {new_selectors ? (
            <div className="sc-selector-pair sc-selector-pair--new">
              <SelectorPill label="container" value={new_selectors.container_selector} accent />
              <SelectorPill label="field" value={new_selectors.field_selector} accent />
            </div>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem', fontStyle: 'italic' }}>
              {failure_reason || 'Waiting…'}
            </span>
          )}
        </div>

      </div>
    </div>
  )
}

function SelectorPill({ label, value, accent }) {
  if (!value) return null
  return (
    <div className="sc-pill">
      <span className="sc-pill-label">{label}</span>
      <span className={`sel-code ${accent ? 'sel-code--accent' : ''}`}>{value}</span>
    </div>
  )
}

function Tag({ label, value, accent }) {
  return (
    <span className={`sc-tag ${accent ? 'sc-tag--accent' : ''}`}>
      <span className="sc-tag-key">{label}:</span> {value}
    </span>
  )
}
