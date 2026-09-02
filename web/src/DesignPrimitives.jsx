export function Masthead({ status, address, storey }) {
  return <header className="masthead">
    <a className="skip-link" href="#study-workbench">Skip to the study</a>
    <div className="maker"><span className="maker-mark" aria-hidden="true">AI</span><span>Apartment Intelligence</span></div>
    <p className="masthead-purpose">A consumer environmental study for an existing HDB home.</p>
    <div className="case-line" aria-label="Current study">
      <span>{address || 'Dawson, Singapore'}</span>
      <span>{storey ? `Storey ${storey}` : 'New study'}</span>
      <span data-state={status}>{status.replace('_', ' ')}</span>
    </div>
  </header>
}

export function StudyProgress({ screens, current, onSelect }) {
  const index = Math.max(0, screens.findIndex(([id]) => id === current))
  return <nav className="study-progress" aria-label="Study journey">
    <p><span>{String(index + 1).padStart(2, '0')}</span> of {String(screens.length).padStart(2, '0')}</p>
    <ol>{screens.map(([id, label], item) => <li key={id}>
      <button aria-current={current === id ? 'step' : undefined} onClick={() => onSelect(id)}>{label}</button>
    </li>)}</ol>
  </nav>
}

export function StudySummary({ study, state }) {
  return <section className="study-summary" aria-labelledby="study-question">
    <div>
      <p className="section-reference">Dawson study · 87 / 141087</p>
      <h1 id="study-question">How does the sun meet this home?</h1>
    </div>
    <p>{study ? `${study.address}, storey ${study.storey}. Inspect the proposed facade, confirm the home you mean, then compare four deterministic environmental studies.` : 'Begin with an HDB address and storey. Public building records establish the context; you identify the apartment geometry the records cannot know.'}</p>
    <dl className="evidence-state">
      <div><dt>Context</dt><dd>Sourced</dd></div>
      <div><dt>Height</dt><dd>Inferred</dd></div>
      <div><dt>Home</dt><dd>{state.status === 'ready' || state.status === 'complete' ? 'Confirmed' : 'Needs you'}</dd></div>
    </dl>
  </section>
}

export function ChapterHeader({ number, title, children }) {
  return <div className="chapter-header"><p className="chapter-number">{number}</p><div><h2>{title}</h2>{children}</div></div>
}

export function ProvenanceDisclosure({ context, result }) {
  return <details className="provenance">
    <summary>Sources, assumptions and method</summary>
    <div className="provenance-grid">
      <p><b>Sourced context</b> HDB Existing Building and HDB Property Information fixture, {context?.fixture_version || 'loading'}.</p>
      <p><b>Inferred massing</b> Maximum floor level × 3.0 m floor-to-floor height.</p>
      <p><b>Human-confirmed geometry</b> Facade, horizontal position, unit zone and window dimensions.</p>
      <p><b>Calculated evidence</b> {result ? `${result.method_version}; result ${result.digest.slice(0, 12)}…` : 'Ladybug solar geometry; analysis awaiting confirmation.'}</p>
    </div>
  </details>
}

export function ReportFooter() {
  return <footer className="report-footer">
    <p>Apartment Intelligence</p>
    <p>Approximate consumer decision support—not valuation, certification, or professional architectural advice.</p>
    <p>Contains information from data.gov.sg under the Singapore Open Data Licence.</p>
  </footer>
}
