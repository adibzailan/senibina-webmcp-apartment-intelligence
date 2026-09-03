import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { exportUrl, liveApi } from "./api";
import { confirmFromClick, createStudy, proposePlacement, runAnalysis, showAnalysis, explainEvidence } from "./actions";
import { cardsPdf, download, svgToPng, zipBlob } from "./cards";
import { initialState, reducer, State } from "./state";
import { Viewer } from "./viewer";
import { registerWebMcp, toolDefinitions } from "./webmcp";

const STEPS: State["screen"][] = ["locate", "place", "confirm", "analysis", "export"];
const DATES = ["03-21", "06-21", "09-22", "12-21"];

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state); stateRef.current = state;
  const ctx = useMemo(() => ({ api: liveApi, dispatch, getState: () => stateRef.current }), []);
  const [context, setContext] = useState<any>(null);
  const [mcp, setMcp] = useState<{ registered: boolean; where: string } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const [glbKey, setGlbKey] = useState<string>("");

  useEffect(() => { liveApi.context().then(setContext).catch(() => setContext({ supported: [] })); }, []);

  useEffect(() => {
    if (!canvasRef.current || viewerRef.current) return;
    try {
      viewerRef.current = new Viewer(canvasRef.current);
      viewerRef.current.loadGlb("/api/context/scene.glb").then(() => viewerRef.current?.preset("precinct")).catch((e) => console.warn(e));
    } catch (e) { console.warn("WebGL unavailable", e); }
    return () => { viewerRef.current?.dispose(); viewerRef.current = null; };
  }, []);

  // scene: reload GLB whenever a placement is staged/confirmed/analysed
  useEffect(() => {
    const key = state.studyId ? `${state.studyId}:${state.placementRevision}:${state.digest ?? ""}` : "";
    if (!viewerRef.current || !state.studyId || !state.placementRevision || key === glbKey) return;
    setGlbKey(key);
    viewerRef.current.loadGlb(`/api/studies/${state.studyId}/scene.glb?r=${state.placementRevision}&d=${state.digest ?? ""}`).then(() => viewerRef.current?.preset(state.view.camera)).catch((e) => console.warn(e));
  }, [state.studyId, state.placementRevision, state.digest]);

  useEffect(() => {
    const v = viewerRef.current; if (!v) return;
    const mode = state.view.preset === "sunpath" ? "shadow" : state.view.preset;
    v.setHeat(state.result, mode as any, state.view.date, state.view.hour);
    v.setSun(state.view.preset === "radiation" ? null : state.result, state.view.date, state.view.hour);
  }, [state.result, state.view]);

  useEffect(() => { viewerRef.current?.preset(state.view.camera); }, [state.view.camera, glbKey]);

  async function exportFromPage(formats: string[]) {
    const s = stateRef.current; if (!s.studyId || !s.result) return { error: "EXPORT_NOT_READY", next_action: "Run the analysis first." };
    const done: string[] = [];
    for (const f of formats) {
      const server: Record<string, string> = { glb: "scene.glb", obj: "analytical.obj", "3dm": "scene.3dm", "evidence.json": "evidence.json", "cards.svg": "cards.svg", zip: "bundle.zip" };
      if (server[f]) { const b = await (await fetch(exportUrl(s.studyId, server[f]))).blob(); download(`apartment-intelligence-${server[f]}`, b); done.push(f); continue; }
      if (f === "pdf") { const svg = await (await fetch(exportUrl(s.studyId, "cards.svg"))).text(); download("apartment-intelligence-cards.pdf", await cardsPdf(svg, viewerRef.current?.snapshot() ?? null, s.digest ?? "")); done.push(f); }
      if (f === "png") { const svg = await (await fetch(exportUrl(s.studyId, "cards.svg"))).text(); download("apartment-intelligence-cards.png", await svgToPng(svg, 1)); done.push(f); }
    }
    return { downloaded: done, note: "Downloads start from the visible page; PNG/PDF are presentation renders." };
  }

  useEffect(() => {
    if (!context) return;
    const defs = toolDefinitions(ctx, context.supported ?? [], exportFromPage);
    const reg = registerWebMcp(defs);
    setMcp({ registered: reg.registered, where: reg.where });
    (window as any).__aiTools = defs; // test hook: lets Playwright call tools without the flag
    return () => reg.abort();
  }, [context]);

  const unit = context?.units?.[state.placement.variant];
  const toggles = unit ? unit.elements.filter((e: any) => ["opening", "balcony", "railing"].includes(e.kind) && (e.kind !== "opening" || e.base_m > 0)) : [];
  const r = state.result;
  const stepIndex = STEPS.indexOf(state.screen) + 1;

  return (
    <div className="container">
      <header className="masthead">
        <h1>Apartment Intelligence</h1>
        <span className="index" aria-live="polite">Step {stepIndex} of 5 · {state.address}, storey {state.storey}{mcp ? ` · WebMCP ${mcp.registered ? "on " + mcp.where : "not exposed by this browser"}` : ""}</span>
      </header>

      {state.screen === "locate" && <h2 className="question">Will this apartment get the sun you expect?</h2>}
      {state.screen === "place" && <h2 className="question">Choose the wing and layout you recognise.</h2>}
      {state.screen === "confirm" && <h2 className="question">Confirm the placement you see.</h2>}
      {state.screen === "analysis" && <h2 className="question">Sun, shade and radiation on your floor.</h2>}
      {state.screen === "export" && <h2 className="question">Keep the evidence.</h2>}

      <div className="workbench">
        <div className="canvas-col">
          <div className="canvas" ref={canvasRef} role="img" aria-label="Three-dimensional precinct model with the target tower and the confirmed apartment">
            <span className="north">N ↑ (+y)</span>
            <span className="edge">{state.view.camera} view · Dawson precinct, ENU metres · {state.view.preset}{r ? ` · ${state.view.date} ${state.view.hour}:00` : ""}</span>
          </div>
          <div className="toolbar" aria-label="Canvas controls">
            {(["precinct", "tower", "home", "plan"] as const).map((c) => <button key={c} aria-pressed={state.view.camera === c} onClick={() => { showAnalysis(ctx, { camera: c }); viewerRef.current?.preset(c); }}>{c}</button>)}
            <button onClick={() => viewerRef.current?.preset("north")}>north</button>
            <button onClick={() => viewerRef.current?.preset(state.view.camera)}>reset</button>
          </div>
          {r && <div className="legend" style={{ marginTop: 8 }}>
            {state.view.preset === "shadow" ? <><span style={{ width: 12, height: 12, background: "#f2c230", display: "inline-block" }} /> lit <span style={{ width: 12, height: 12, background: "#45534d", display: "inline-block" }} /> shaded</> : <><span>{state.view.preset === "radiation" ? "0" : "0 h"}</span><span className="ramp" /><span>{state.view.preset === "radiation" ? `${r.radiation.max} kWh/m² per year` : "hours of direct sun"}</span></>}
            <span style={{ marginLeft: "auto" }}>{r.sensors.count} sensors at {r.sensors.grid.spacing_m} m · plane 0.8 m</span>
          </div>}
        </div>

        <aside className="rail">
          {state.screen === "locate" && <section>
            <label htmlFor="address">Address or postal code</label>
            <div className="field"><input id="address" list="homes" value={state.address} onChange={(e) => dispatch({ type: "set_address", address: e.target.value })} /></div>
            <datalist id="homes">{(context?.supported ?? []).map((h: any) => <option key={h.postal_code} value={h.address} />)}</datalist>
            <label htmlFor="storey">Storey</label>
            <div className="field"><input id="storey" type="number" min={2} max={47} value={state.storey} onChange={(e) => dispatch({ type: "set_storey", storey: Number(e.target.value) })} /></div>
            <p className="status">This build covers SkyVille @ Dawson Block 87 (postal 141087), storeys 2 to 47. Storey 30 is the worked example; no storey-30 plan is published, so the plate is inferred.</p>
            <button className="primary" disabled={!!state.busy} onClick={() => createStudy(ctx, state.address, state.storey).catch(() => {})}>Start the study</button>
          </section>}

          {(state.screen === "place" || state.screen === "confirm") && <section>
            <label>Wing (facade)</label>
            <div className="field"><select value={state.placement.facade} onChange={(e) => dispatch({ type: "set_placement", placement: { facade: e.target.value as any } })}>{["NE", "NW", "SW", "SE"].map((f) => <option key={f}>{f}</option>)}</select></div>
            <label>4-room stack position in the wing (assumed)</label>
            <div className="field"><select value={state.placement.stack_position} onChange={(e) => dispatch({ type: "set_placement", placement: { stack_position: e.target.value as any } })}><option value="end">wing tip</option><option value="inner">near the core</option></select></div>
            <label>Published layout</label>
            <div className="field"><select value={state.placement.variant} onChange={(e) => dispatch({ type: "set_placement", placement: { variant: e.target.value as any } })}><option value="A">Type A, three bedrooms</option><option value="B">Type B, larger living</option><option value="C">Type C, master suite</option></select></div>
            <label className="checks" style={{ marginTop: 8 }}><input type="checkbox" checked={state.placement.mirrored} onChange={(e) => dispatch({ type: "set_placement", placement: { mirrored: e.target.checked } })} /> Mirrored plan</label>
            <details><summary>Windows, balcony and railings (assumed unless published)</summary>
              <div className="checks" style={{ marginTop: 8 }}>{toggles.map((e: any) => <label key={e.id}><input type="checkbox" checked={state.placement.openings[e.id] ?? e.enabled_by_default} onChange={(ev) => dispatch({ type: "set_placement", placement: { openings: { [e.id]: ev.target.checked } } })} /> {e.id} <span style={{ color: "var(--ink-muted)" }}>({e.source.state})</span></label>)}</div>
            </details>
            <div className="toolbar">
              <button className="primary" disabled={!!state.busy} onClick={() => proposePlacement(ctx, {}).catch(() => {})}>Stage this placement</button>
              {state.screen === "confirm" && <button className="confirm" data-testid="confirm-button" disabled={!!state.busy || state.placementRevision === 0} onClick={(ev) => confirmFromClick(ctx, ev.isTrusted && (navigator as any).userActivation?.isActive !== false).catch(() => {})}>I confirm this is my apartment</button>}
            </div>
            {state.screen === "confirm" && <p className="confirm-sentence">You are confirming the {state.placement.facade} wing, {state.placement.stack_position === "end" ? "wing-tip" : "inner"} stack, Type {state.placement.variant}{state.placement.mirrored ? ", mirrored" : ""}, on storey {state.storey}. A tool cannot do this for you.</p>}
          </section>}

          {(state.screen === "analysis" || state.screen === "export") && <section>
            {!r && <div className="toolbar">
              <button className="primary" disabled={!!state.busy} onClick={() => runAnalysis(ctx, 0.25).catch(() => {})}>Run the analysis (0.25 m grid)</button>
              <button disabled={!!state.busy} onClick={() => runAnalysis(ctx, 0.5).catch(() => {})}>Fast (0.5 m)</button>
            </div>}
            {r && <>
              <label>Study</label>
              <div className="toolbar">{(["sunpath", "shadow", "solar_access", "radiation"] as const).map((p) => <button key={p} aria-pressed={state.view.preset === p} onClick={() => showAnalysis(ctx, { preset: p })}>{p.replace("_", " ")}</button>)}</div>
              <label>Date and hour</label>
              <div className="field">
                <select value={state.view.date} onChange={(e) => showAnalysis(ctx, { date: e.target.value })}>{DATES.map((d) => <option key={d}>{d}</option>)}</select>
                <select value={state.view.hour} onChange={(e) => showAnalysis(ctx, { hour: Number(e.target.value) })}>{[9, 12, 15, 17].map((h) => <option key={h} value={h}>{h}:00</option>)}</select>
              </div>
              <div className="numbers" style={{ marginTop: 12 }}>
                <div><span>minimum</span><strong>{r.radiation.min}</strong></div><div><span>average</span><strong>{r.radiation.avg}</strong></div><div><span>maximum</span><strong>{r.radiation.max}</strong></div>
              </div>
              <p className="status">kWh/m² per year on the 0.8 m plane · {r.sky.discretisation} sky, {r.sky.patches} patches · {r.weather.station} TMYx · digest {r.digest.slice(0, 12)}</p>
              <details><summary>Method, sources and limitations</summary>
                <table className="evidence"><tbody>
                  {r.provenance.map((p: any, i: number) => <tr key={i}><td>{String(p.value)}</td><td>{p.state}</td><td>{p.method}</td><td>{p.limitation ?? ""}</td></tr>)}
                  {r.radiation.limitations.map((l: string, i: number) => <tr key={"l" + i}><td colSpan={4}>{l}</td></tr>)}
                </tbody></table>
              </details>
              <div className="toolbar"><button className="primary" onClick={() => dispatch({ type: "go", screen: "export" })}>Export</button></div>
            </>}
          </section>}

          {state.screen === "export" && r && <section>
            <div className="toolbar">
              {["glb", "obj", "3dm", "evidence.json", "cards.svg", "png", "pdf", "zip"].map((f) => <button key={f} onClick={() => exportFromPage([f])}>{f}</button>)}
            </div>
            <p className="status">SVG, GLB, OBJ and evidence.json are byte-stable and bound to the digest. PNG and PDF are presentation renders. 3DM embeds fresh object ids.</p>
          </section>}

          <p className={"status" + (state.message?.kind === "error" ? " error" : "")} role="status" aria-live="polite">{state.busy ? `${state.busy}…` : state.message?.text ?? (state.studyId ? `Study ${state.studyId} · ${state.studyState}` : "")}</p>
          {state.lastActor === "webmcp" && <p className="status">Last change came from a WebMCP tool; the page state is what you see.</p>}
        </aside>
      </div>

      {r && <section className="chapter">
        <h2>Per room</h2>
        <table className="evidence"><tbody>{Object.entries(r.radiation.per_room).map(([k, v]: any) => <tr key={k}><td>{k}</td><td>{v.sensors} sensors</td><td>min {v.min}</td><td>avg {v.avg}</td><td>max {v.max}</td></tr>)}</tbody></table>
        <details style={{ marginTop: 8 }}><summary>Explain evidence (same record a tool receives)</summary><pre style={{ fontSize: 11, whiteSpace: "pre-wrap" }}>{JSON.stringify(explainEvidence(ctx, "digest"), null, 1)}</pre></details>
      </section>}
      <footer className="status">Footprints and storey counts: HDB via data.gov.sg, Singapore Open Data Licence v1.0. No endorsement by HDB, OneMap or the Singapore Government. Not a valuation, compliance or daylight certification.</footer>
    </div>
  );
}
