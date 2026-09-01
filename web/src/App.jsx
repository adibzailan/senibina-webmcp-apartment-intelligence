import { useEffect, useReducer, useRef, useState } from 'react'
import { api } from './api'
import { exportBundle } from './artifacts'
import Scene from './Scene'
import { initialState, reduce } from './state'
import { registerWebMCP } from './webmcp'


const screens = [['provide', 'Provide apartment'], ['verify', 'Research & verify'], ['locate', 'Locate home'], ['analyse', 'Explore the sun'], ['export', 'Keep the evidence']]

export default function App() {
  const [state, dispatch] = useReducer(reduce, initialState)
  const current = useRef(state); current.current = state
  const [context, setContext] = useState(null)
  const [study, setStudy] = useState(null)
  const [result, setResult] = useState(null)
  const [message, setMessage] = useState('Ready for one reproducible Dawson study.')

  useEffect(() => { const c = new AbortController(); api.context(c.signal).then(setContext); return () => c.abort() }, [])
  useEffect(() => { if (!state.studyId) return; const c = new AbortController(); api.state(state.studyId, c.signal).then(setStudy); return () => c.abort() }, [state.studyId, state.status, state.revision])
  useEffect(() => { if (state.status !== 'complete' || !state.studyId) return; const c = new AbortController(); api.result(state.studyId, c.signal).then(setResult); return () => c.abort() }, [state.status, state.studyId])
  const download = async (studyId) => {
    if (!studyId) throw new Error('EXPORT_NOT_READY')
    const completed = result || await api.result(studyId)
    const zip = await exportBundle(completed, await api.model(studyId))
    const link = document.createElement('a'); link.href = URL.createObjectURL(zip); link.download = 'apartment-intelligence.zip'; link.click(); URL.revokeObjectURL(link.href)
    dispatch({ type: 'show-screen', screen: 'export' })
    return { study_id: studyId, state: 'complete', outcome: 'Downloaded the evidence bundle.', next_action: 'Open the ZIP and review its provenance.' }
  }
  useEffect(() => { let cleanup = () => {}; registerWebMCP(dispatch, () => current.current, download).then(fn => cleanup = fn).catch(error => { document.documentElement.dataset.webmcpError = error.name; setMessage(`WebMCP registration failed: ${error.message}`) }); return () => cleanup() }, [])

  const create = async event => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try { const result = await api.create({ address: form.get('address'), storey: Number(form.get('storey')) }); dispatch({ type: 'study-created', payload: result, source: 'ui' }); setStudy(await api.state(result.study_id)); setMessage(result.next_action) }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }
  const confirm = async event => {
    if (!event.isTrusted || !navigator.userActivation?.isActive) return setMessage('Confirmation needs your direct click.')
    try { const result = await api.confirm(state.studyId, study.proposal_revision); dispatch({ type: 'study-state', payload: result, source: 'ui' }); setStudy(await api.state(state.studyId)); setMessage(result.next_action) }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }
  const propose = async event => {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try {
      const payload = { facade: form.get('facade'), position: form.get('position'), width: Number(form.get('width')), window_width: Number(form.get('window_width')), window_height: Number(form.get('window_height')), sill_height: Number(form.get('sill_height')) }
      const response = await api.proposal(state.studyId, payload); dispatch({ type: 'study-state', payload: response, source: 'ui' }); setStudy(await api.state(state.studyId)); setMessage(response.next_action)
    } catch (error) { setMessage(error.body?.next_action || error.message) }
  }
  const analyse = async () => {
    try { const response = await api.analyse(state.studyId); dispatch({ type: 'study-state', payload: response, source: 'ui' }); setResult(await api.result(state.studyId)); setMessage('Four deterministic studies completed.') }
    catch (error) { setMessage(error.body?.next_action || error.message) }
  }

  return <main data-webmcp={String(Boolean(document.modelContext))}>
    <header><span className="eyebrow">SENIBINA / CONSUMER ENVIRONMENTAL STUDY</span><h1>Apartment<br/><i>Intelligence</i></h1><p>See how the sun meets a home before you choose it.</p></header>
    <nav aria-label="Study journey">{screens.map(([id, label], index) => <button key={id} aria-current={state.screen === id ? 'step' : undefined} onClick={() => dispatch({ type: 'show-screen', screen: id })}><b>0{index + 1}</b>{label}</button>)}</nav>
    <section className="workspace">
      <div className="stage"><Scene context={context} study={study} result={result} analysis={state.analysis}/>{result && state.screen === 'analyse' && <div className="analysis-readout"><b>{state.analysis.replace('_', ' ')}</b>{state.analysis === 'radiation' && <span>{result.radiation.average_kwh_m2} kWh/m² average</span>}{state.analysis === 'solar_access' && <span>{result.solar_access['2026-03-21'].total_hours} direct-sun hours · 21 Mar</span>}{state.analysis === 'shadow' && <span>{result.shadow.samples.map(item => `${item.time} ${Math.round(item.sunlit_fraction * 100)}%`).join(' · ')}</span>}{state.analysis === 'sunpath' && <span>Equinoxes + solstices · Singapore time</span>}</div>}<div className="legend"><span>Sourced context</span><span>Inferred massing</span><span>Human-confirmed home</span></div></div>
      <aside>
        {state.screen === 'provide' && <><p className="kicker">01 / PROVIDE</p><h2>Begin with the home.</h2><form onSubmit={create}><label>HDB address<input name="address" defaultValue="87 Dawson Road" required /></label><label>Storey<input name="storey" type="number" min="1" max="47" defaultValue="30" required /></label><button className="primary">Research this apartment</button></form></>}
        {state.screen === 'verify' && <><p className="kicker">02 / RESEARCH</p><h2>What we know—and what we don't.</h2><dl><dt>Sourced</dt><dd>HDB footprint and maximum floor level</dd><dt>Inferred</dt><dd>141 m height from 47 × 3.0 m</dd><dt>Needs you</dt><dd>Exact facade, unit zone and openings</dd></dl><button className="primary" onClick={() => dispatch({ type: 'show-screen', screen: 'locate' })}>Locate my home in 3D</button></>}
        {state.screen === 'locate' && study && <><p className="kicker">03 / LOCATE</p><h2>Place the home you mean.</h2><form className="proposal" onSubmit={propose}><label>Facade<select name="facade" defaultValue={study.proposal.facade}><option>north</option><option>east</option><option>south</option><option>west</option></select></label><label>Position<select name="position" defaultValue={study.proposal.position}><option>left</option><option>centre</option><option>right</option></select></label><label>Unit zone (m)<input name="width" type="number" min="2" max="20" step=".5" defaultValue={study.proposal.width}/></label><label>Window width (m)<input name="window_width" type="number" min=".5" max="12" step=".1" defaultValue={study.proposal.window_width}/></label><label>Window height (m)<input name="window_height" type="number" min=".5" max="3" step=".1" defaultValue={study.proposal.window_height}/></label><label>Sill height (m)<input name="sill_height" type="number" min="0" max="2" step=".1" defaultValue={study.proposal.sill_height}/></label><button className="secondary">Update visible proposal</button></form><p className="proposal-summary"><span>{study.proposal.facade} facade · {study.proposal.position} zone</span><span>storey {study.storey} · {study.proposal.window_width} × {study.proposal.window_height} m window</span></p><button className="primary confirm" onClick={confirm}>Confirm this home</button><small>This direct human action is never available to an agent.</small></>}
        {state.screen === 'analyse' && <><p className="kicker">04 / EXPLORE</p><h2>The sun, made legible.</h2><div className="studies">{['sunpath','shadow','solar_access','radiation'].map(name => <button aria-pressed={state.analysis === name} key={name} onClick={() => dispatch({ type: 'show-analysis', analysis: name })}>{name.replace('_', ' ')}</button>)}</div><div className="result"><b>{state.analysis.replace('_', ' ')}</b><p>{result ? 'Computed result shown in the shared scene.' : 'Ready only after the resident confirms the visible unit.'}</p></div><button className="primary" disabled={state.status !== 'ready'} onClick={analyse}>{state.status === 'complete' ? 'Analysis complete' : 'Run all four studies'}</button></>}
        {state.screen === 'export' && <><p className="kicker">05 / KEEP</p><h2>Evidence you can carry forward.</h2><p>Five distinct 1600 × 2400 cards, one five-page PDF, provenance, and reusable layered geometry.</p><button className="primary" disabled={state.status !== 'complete'} onClick={() => download(state.studyId)}>Download evidence ZIP</button></>}
        <p className="status" role="status">{message}</p>
      </aside>
    </section>
    <footer>Approximate consumer decision support. Not valuation, certification, or professional architectural advice. Contains information from data.gov.sg under the Singapore Open Data Licence.</footer>
  </main>
}
