import './PipelineFlow.css'

const ALL_STEPS = [
  { key: 'LOADING_PAGE',         label: 'Loading Page',      icon: '🌐', group: 'normal'  },
  { key: 'CONNECTED',            label: 'Connected',         icon: '🔗', group: 'normal'  },
  { key: 'SCRAPING',             label: 'Scraping',          icon: '⚡', group: 'normal'  },
  { key: 'FAILURE_DETECTED',     label: 'Failure Detected',  icon: '⚠️', group: 'alarm'   },
  { key: 'ANALYZING',            label: 'Analyzing DOM',     icon: '🔍', group: 'healing' },
  { key: 'GENERATING_CANDIDATES',label: 'Generating',        icon: '🧠', group: 'healing' },
  { key: 'OPTIMIZING',           label: 'Optimizing',        icon: '⚛️', group: 'healing' },
  { key: 'VALIDATING',           label: 'Validating',        icon: '🧪', group: 'healing' },
  { key: 'REPAIRED',             label: 'Selector Found',    icon: '✅', group: 'healed'  },
  { key: 'RESUMED',              label: 'Resumed',           icon: '🚀', group: 'healed'  },
]

export default function PipelineFlow({ pipelineStep, stepsDone = [] }) {
  const doneSet = new Set(stepsDone)
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Pipeline Flow</span>
        <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          DETECT → UNDERSTAND → OPTIMIZE → VALIDATE → REPAIR → RESUME
        </span>
      </div>
      <div className="pf-track">
        {ALL_STEPS.map((step, idx) => {
          const done    = doneSet.has(step.key)
          const current = pipelineStep === step.key
          return (
            <div key={step.key} className={`pf-step pf-step--${step.group} ${done ? 'pf-step--done' : ''} ${current ? 'pf-step--active' : ''}`}>
              {idx > 0 && <div className={`pf-line ${done ? 'pf-line--done' : ''}`} />}
              <div className="pf-node">
                <span className="pf-num">{idx + 1}</span>
                <span className="pf-icon">{step.icon}</span>
                {current && <span className="pf-ring" />}
              </div>
              <span className="pf-label">{step.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
