import { useEffect, useReducer, useRef, useState } from 'react'
import { api } from './api'
import { exportBundle } from './artifacts'
import { ChapterHeader, Masthead, ProvenanceDisclosure, ReportFooter, StudyProgress, StudySummary } from './DesignPrimitives'
import Scene from './Scene'
import { initialState, reduce } from './state'
import { registerWebMCP } from './webmcp'

const screens = [['provide', 'Provide apartment'], ['verify', 'Research and verify'], ['locate', 'Locate home'], ['analyse', 'Explore the sun'], ['export', 'Keep the evidence']]
const analyses = [
  ['sunpath', 'Sunpath', 'Seasonal paths'],
  ['shadow', 'Shadow', 'Three daily moments'],
  ['solar_access', 'Solar Access', 'Four seasonal dates'],
  ['radiation', 'Radiation', 'Interior floor exposure'],
]

export default function App() {
  const [state, dispatch] = useReducer(reduce, initialState)
  const current = useRef(state); current.current = state
  const [context, setContext] = useState(null)
  const [study, setStudy] = useState(null)
  const [result, setResult] = useState(null)
  const [message, setMessage] = useState('Ready for one reproducible Dawson study.')
  const live = useRef({ context, study, result }); live.current = { context, study, result }

  useEffect(() => { const c = new AbortController(); api.context(c.signal).then(setContext); return () => c.abort() }, [])
  useEffect(() => { if (!state.studyId) return; const c = new AbortController(); api.state(state.studyId, c.signal).then(setStudy); return () => c.abort() }, [state.studyId, state.status, state.revision])
  useEffect(() => { if (state.status !== 'complete' || !state.studyId) return; const c = new AbortController(); api.result(state.studyId, c.signal).then(setResult); return () => c.abort() }, [state.status, state.studyId])

  const download = async studyId => {
    if (!studyId) throw new Error('EXPORT_NOT_READY')
    const [completed, model, requestedStudy, requestedContext] = await Promise.all([api.result(studyId), api.model(studyId), api.state(studyId), live.current.context ? Promise.resolve(live.current.context) : api.context()])
    if (live.current.study && live.current.study.study_id !== studyId) throw new Error('CROSS_STUDY_EXPORT')
    const zip = await exportBundle(completed, model, { context: requestedContext, study: requestedStudy })
    const link = document.createElement('a'); link.href = URL.createObjectURL(zip); link.download = 'apartment-intelligence.zip'; link.click(); URL.revokeObjectURL(link.href)
    dispatch({ type: 'show-screen', screen: 'export' })
    return { study_id: studyId, state: 'complete', outcome: 'Downloaded the evidence bundle.', next_action: 'Open the ZIP and review its provenance.' }
  }

  useEffect(() => { let cleanup = () => {}; registerWebMCP(dispatch, () => current.current, download).then(fn => cleanup = fn).catch(error => { document.documentElement.dataset.webmcpError = error.name; setMessage(`WebMCP registration failed: ${error.message}`) }); return () => cleanup() }, [])

  const create = async event => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try { const response = await api.create({ address: form.get('address'), storey: Number(form.get('storey')) }); dispatch({ type: 'study-created', payload: response, source: 'ui' }); setStudy(await api.state(response.study_id)); setMessage(response.next_action) }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }

  const confirm = async event => {
    if (!event.isTrusted || !navigator.userActivation?.isActive) return setMessage('Confirmation needs your direct click.')
    try { const response = await api.confirm(state.studyId, study.proposal_revision); dispatch({ type: 'study-state', payload: response, source: 'ui' }); dispatch({ type: 'show-screen', screen: 'analyse', source: 'ui' }); setStudy(await api.state(state.studyId)); setMessage(response.next_action) }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }

  const propose = async event => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try {
      const payload = { facade: form.get('facade'), position: form.get('position'), width: Number(form.get('width')), depth: Number(form.get('depth')), window_width: Number(form.get('window_width')), window_height: Number(form.get('window_height')), sill_height: Number(form.get('sill_height')) }
      const response = await api.proposal(state.studyId, payload); dispatch({ type: 'study-state', payload: response, source: 'ui' }); setStudy(await api.state(state.studyId)); setMessage(response.next_action)
    } catch (error) { setMessage(error.body?.next_action || error.message) }
  }

  const analyse = async () => {
    try { const response = await api.analyse(state.studyId); dispatch({ type: 'study-state', payload: response, source: 'ui' }); setResult(await api.result(state.studyId)); setMessage('Four deterministic studies completed.') }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }

  const openAnalysis = name => dispatch({ type: 'show-analysis', analysis: name, source: 'ui' })

  return <main data-webmcp={String(Boolean(document.modelContext))}>
    <Masthead status={state.status} address={study?.address} storey={study?.storey}/>
    <StudyProgress screens={screens} current={state.screen} onSelect={screen => dispatch({ type: 'show-screen', screen })}/>
    <StudySummary study={study} state={state}/>

    <section className="workbench" id="study-workbench" aria-label="Apartment study workbench">
      <div className="architectural-stage">
        <Scene context={context} study={study} result={result} analysis={state.screen === 'analyse' || state.screen === 'export' ? state.analysis : 'site'} screen={state.screen}
          shadowTime={state.shadowTime} solarDate={state.solarDate} viewRequest={state.viewRequest} viewRevision={state.viewRevision}
          onView={view => dispatch({ type: 'show-view', view, source: 'ui' })}/>
        <div className="drawing-caption">
          <p><b>Fig. 01</b> Dawson precinct massing, local metre coordinates. North is up in plan.</p>
          <p>{state.screen !== 'analyse' && state.screen !== 'export' ? 'Public footprint context with inferred height and a resident-defined home.' : `Calculated ${state.analysis.replace('_', ' ')} evidence shown on the shared scene.`}</p>
        </div>
      </div>

      <aside className="reading-rail" aria-label="Current study controls">
        {state.screen === 'provide' && <section>
          <ChapterHeader number="01" title="Begin with the home."><p>The address finds the public context. The storey places the proposed unit vertically.</p></ChapterHeader>
          <form onSubmit={create}><label>HDB address<input name="address" defaultValue="87 Dawson Road" required /></label><label>Storey<input name="storey" type="number" min="1" max="47" defaultValue="30" required /></label><button className="primary">Research this apartment</button></form>
        </section>}

        {state.screen === 'verify' && <section>
          <ChapterHeader number="02" title="Separate records from assumptions."><p>The public record establishes the building. It cannot identify a private unit or its windows.</p></ChapterHeader>
          <dl className="fact-list"><div><dt>Sourced</dt><dd>HDB footprint and maximum floor level.</dd></div><div><dt>Inferred</dt><dd>141 m height from 47 floors × 3.0 m.</dd></div><div><dt>Needs you</dt><dd>Exact facade, unit zone and openings.</dd></div></dl>
          <button className="primary" onClick={() => dispatch({ type: 'show-screen', screen: 'locate' })}>Locate the home in 3D</button>
        </section>}

        {state.screen === 'locate' && study && <section>
          <ChapterHeader number="03" title="Place the apartment you recognise."><p>Adjust the approximate floor plate and its exterior opening. Red appears only after you confirm this is the home you mean.</p></ChapterHeader>
          <form className="proposal" onSubmit={propose}>
            <label>Facade<select name="facade" defaultValue={study.proposal.facade}><option>north</option><option>east</option><option>south</option><option>west</option></select></label>
            <label>Position<select name="position" defaultValue={study.proposal.position}><option>left</option><option>centre</option><option>right</option></select></label>
            <label>Unit zone (m)<input name="width" type="number" min="2" max="20" step=".5" defaultValue={study.proposal.width}/></label>
            <label>Apartment depth (m)<input name="depth" type="number" min="2" max="12" step=".5" defaultValue={study.proposal.depth}/></label>
            <label>Window width (m)<input name="window_width" type="number" min=".5" max="12" step=".1" defaultValue={study.proposal.window_width}/></label>
            <label>Window height (m)<input name="window_height" type="number" min=".5" max="3" step=".1" defaultValue={study.proposal.window_height}/></label>
            <label>Sill height (m)<input name="sill_height" type="number" min="0" max="2" step=".1" defaultValue={study.proposal.sill_height}/></label>
            <button className="secondary">Update the visible proposal</button>
          </form>
          <p className="proposal-summary"><span>{study.proposal.facade} facade · {study.proposal.position} zone · {study.proposal.width} × {study.proposal.depth} m</span><span>{study.plate_summary?.usable_area_m2} m² usable grid · {study.plate_summary?.spacing_m} m sensors · {study.plate_summary?.normal_state?.replaceAll('_', ' ')}</span><span>storey {study.storey} · {study.proposal.window_width} × {study.proposal.window_height} m window</span></p>
          <button className="primary confirmation" onClick={confirm}>Confirm this home</button>
          <p className="human-boundary">Confirm in this visible interface. Confirmation is not exposed as a WebMCP tool; it is an interaction boundary, not identity proof.</p>
        </section>}

        {state.screen === 'analyse' && <section>
          <ChapterHeader number="04" title="Read the sun as evidence."><p>Each view uses the same confirmed geometry and deterministic result digest.</p></ChapterHeader>
          <div className="analysis-index">{analyses.map(([name, label, note], index) => <button aria-pressed={state.analysis === name} key={name} onClick={() => openAnalysis(name)}><span>{String(index + 1).padStart(2, '0')}</span><b>{label}</b><small>{note}</small></button>)}</div>
          {state.analysis === 'shadow' && <fieldset className="time-selector"><legend>Shadow time</legend>{['09:00', '12:00', '15:00'].map(time => <button type="button" key={time} aria-pressed={state.shadowTime === time} onClick={() => dispatch({ type: 'show-analysis', analysis: 'shadow', shadowTime: time, source: 'ui' })}>{time}</button>)}</fieldset>}
          {state.analysis === 'solar_access' && <fieldset className="time-selector"><legend>Seasonal date</legend>{['2026-03-21', '2026-06-21', '2026-09-21', '2026-12-21'].map(date => <button type="button" key={date} aria-pressed={state.solarDate === date} onClick={() => dispatch({ type: 'show-analysis', analysis: 'solar_access', solarDate: date, source: 'ui' })}>{date.slice(5)}</button>)}</fieldset>}
          <AnalysisReading analysis={state.analysis} result={result} status={state.status} shadowTime={state.shadowTime} solarDate={state.solarDate}/>
          <button className="primary" disabled={state.status !== 'ready'} onClick={analyse}>{state.status === 'complete' ? 'Analysis complete' : 'Run all four studies'}</button>
        </section>}

        {state.screen === 'export' && <section>
          <ChapterHeader number="05" title="Keep the evidence."><p>One coherent visual system carries the result from live study to reusable architectural material.</p></ChapterHeader>
          <ul className="export-list"><li>Five 1600 × 2400 PNG evidence cards</li><li>Five-page PDF report</li><li>Layered metre-unit Rhino model</li><li>Manifest, method and result digest</li></ul>
          <button className="primary" disabled={state.status !== 'complete'} onClick={() => download(state.studyId)}>Download the evidence ZIP</button>
        </section>}
        <p className="status" role="status">{message}</p>
      </aside>
    </section>

    {result && <section className="evidence-chapters" aria-labelledby="evidence-heading">
      <div className="evidence-intro"><p className="section-reference">Environmental evidence</p><h2 id="evidence-heading">Four readings of the same home.</h2><p>The diagrams are different because each answers a different question. They share geometry, weather and one result digest.</p></div>
      {analyses.map(([name, label, note], index) => <article key={name} className="evidence-chapter"><p>{String(index + 1).padStart(2, '0')}</p><h3>{label}</h3><p>{note}. <button className="text-action" onClick={() => openAnalysis(name)}>Open this evidence in the viewer</button></p></article>)}
    </section>}

    <ProvenanceDisclosure context={context} result={result}/>
    <ReportFooter/>
  </main>
}

function AnalysisReading({ analysis, result, status, shadowTime, solarDate }) {
  if (!result) return <div className="analysis-reading"><p className="section-reference">{status === 'ready' ? 'Ready to calculate' : 'Awaiting confirmation'}</p><p>{status === 'ready' ? 'The resident-confirmed geometry is ready for the four deterministic studies.' : 'The four studies become available after the resident confirms the visible home.'}</p></div>
  if (analysis === 'sunpath') return <div className="analysis-reading"><p className="section-reference">Seasonal solar geometry</p><p>Equinoxes and solstices, Singapore time. The high tropical paths explain why facade direction matters more than a simple south-facing rule.</p></div>
  if (analysis === 'shadow') { const sample = result.shadow.samples.find(item => item.time === shadowTime); return <div className="analysis-reading"><p className="section-reference">21 March · {shadowTime}</p><p><strong>{sample.sun_patch_area_m2.toFixed(1)} m²</strong> of direct sun reaches the approximate apartment floor. Solar altitude {sample.altitude}°, azimuth {sample.azimuth}°.</p></div> }
  if (analysis === 'solar_access') return <div className="analysis-reading"><p className="section-reference">{solarDate} · direct sun</p><p><strong>{result.solar_access[solarDate].total_hours.toFixed(1)} hours</strong> averaged across the confirmed floor plate at 30-minute intervals.</p></div>
  return <div className="analysis-reading"><p className="section-reference">Approximate interior solar exposure through the window</p><p><strong>{result.radiation.average_kwh_m2} kWh/m²</strong> average across the floor plate. Direct and isotropic diffuse EPW radiation are aperture- and obstruction-tested; glazing and reflections are excluded.</p></div>
}
