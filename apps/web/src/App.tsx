import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { exportUrl, liveApi } from "./api";
import { confirmFromClick, createStudy, proposePlacement, runAnalysis, showAnalysis, explainEvidence } from "./actions";
import { cardsPdf, download, svgToPng, zipBlob } from "./cards";
import { initialState, reducer, State } from "./state";
import { Viewer } from "./viewer";
import { plateSlots } from "./slots";
import { registerWebMcp, toolDefinitions } from "./webmcp";

const STEPS: State["screen"][] = ["locate", "place", "confirm", "analysis", "export"];
const DATES = ["03-21", "06-21", "09-22", "12-21"];
const STATE_WORDS: Record<string, string> = { created: "started", placed: "placement staged", needs_confirmation: "awaiting your confirmation", ready: "confirmed, ready to analyse", analysing: "analysing", analysed: "analysed" };
const ELEMENT_LABELS: Record<string, string> = { "win-mainbed": "Main bedroom window", "win-bed2": "Bedroom 2 window", "win-bed3": "Bedroom 3 window", "win-living": "Living room window", "win-living-side": "Living room side window", "win-mainbed-side": "Main bedroom side window", "win-kitchen": "Kitchen window", "railing-serviceyard": "Service yard railing", "balcony-living": "Living room balcony", "railing-balcony": "Balcony railing" };
const labelOf = (id: string) => ELEMENT_LABELS[id] ?? id.replace(/[-_]/g, " ");

/** A step is reachable only when the state behind it exists; confirmation still needs the click. */
function canAdvance(s: State): boolean {
  switch (s.screen) {
    case "locate": return !!s.studyId;
    case "place": return s.placementRevision > 0;
    case "confirm": return s.confirmedRevision !== null && s.confirmedRevision === s.placementRevision;
    case "analysis": return !!s.result;
    default: return false;
  }
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state); stateRef.current = state;
  const ctx = useMemo(() => ({ api: liveApi, dispatch, getState: () => stateRef.current }), []);
  const [context, setContext] = useState<any>(null);
  const [mcp, setMcp] = useState<{ registered: boolean; where: string } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const [glbKey, setGlbKey] = useState<string>("");
  const framedFor = useRef<string>("");
  const [basemap, setBasemap] = useState(true);
  const compassRef = useRef<SVGSVGElement>(null);

  useEffect(() => { liveApi.context().then(setContext).catch(() => setContext({ supported: [] })); }, []);
  useEffect(() => {
    const v = viewerRef.current; const o = context?.frame?.origin_wgs84; if (!v || !o) return;
    v.loadBasemap(o[0], o[1]).catch((e) => console.warn("basemap", e));
  }, [context]);
  useEffect(() => { viewerRef.current?.setBasemapVisible(basemap); }, [basemap]);

  useEffect(() => {
    if (!canvasRef.current || viewerRef.current) return;
    try {
      viewerRef.current = new Viewer(canvasRef.current);
      viewerRef.current.onFrame = (az) => { if (compassRef.current) compassRef.current.style.transform = `rotate(${-az}deg)`; };
      viewerRef.current.loadGlb("/api/context/scene.glb").then(() => viewerRef.current?.preset("precinct")).catch((e) => console.warn(e));
    } catch (e) { console.warn("WebGL unavailable", e); }
    return () => { viewerRef.current?.dispose(); viewerRef.current = null; };
  }, []);

  // scene: reload GLB whenever a placement is staged/confirmed/analysed
  useEffect(() => {
    const key = state.studyId ? `${state.studyId}:${state.placementRevision}:${state.digest ?? ""}` : "";
    if (!viewerRef.current || !state.studyId || !state.placementRevision || key === glbKey) return;
    setGlbKey(key);
    viewerRef.current.loadGlb(`/api/studies/${state.studyId}/scene.glb?r=${state.placementRevision}&d=${state.digest ?? ""}`).then(() => {
      const v = viewerRef.current; if (!v) return;
      // frame once per stage: a tower-level plan while placing; the apartment once analysed. Never re-frame on every reload.
      const stage = state.result ? "analysed" : "placing";
      if (framedFor.current !== `${state.studyId}:${stage}`) {
        framedFor.current = `${state.studyId}:${stage}`;
        if (stage === "placing") { dispatch({ type: "set_view", view: { camera: "plan" } }); v.preset("plan", "tower"); }
        else { dispatch({ type: "set_view", view: { camera: "home" } }); v.preset("home", "home"); }
      }
    }).catch((e) => console.warn(e));
  }, [state.studyId, state.placementRevision, state.digest]);

  useEffect(() => {
    const v = viewerRef.current; if (!v) return;
    const mode = state.view.preset === "sunpath" ? "shadow" : state.view.preset;
    v.setHeat(state.result, mode as any, state.view.date, state.view.hour);
    v.setSun(state.view.preset === "radiation" ? null : state.result, state.view.date, state.view.hour);
  }, [state.result, state.view]);

  const focus: "home" | "tower" = state.result ? "home" : "tower";

  // live staging: any placement change on the Place/Confirm screens re-stages after a short pause
  const placementKey = JSON.stringify(state.placement);
  const stagedKey = useRef<string>("");
  useEffect(() => {
    if (!state.studyId || !(state.screen === "place" || state.screen === "confirm")) return;
    if (stagedKey.current === placementKey) return;
    const t = setTimeout(() => { stagedKey.current = placementKey; proposePlacement(ctx, {}).catch(() => {}); }, 250);
    return () => clearTimeout(t);
  }, [placementKey, state.studyId, state.screen]);

  // pickable slots on the tower while placing
  const slots = useMemo(() => (context?.plate ? plateSlots(context.plate, state.storey) : []), [context, state.storey]);
  useEffect(() => {
    const v = viewerRef.current; if (!v) return;
    const placing = state.screen === "place" || state.screen === "confirm";
    v.setSlots(placing ? slots : [], `${state.placement.facade}:${state.placement.stack_position}`, placing ? (id) => { const [facade, stack_position] = id.split(":"); dispatch({ type: "set_placement", placement: { facade: facade as any, stack_position: stack_position as any } }); } : null);
  }, [slots, state.screen, state.placement.facade, state.placement.stack_position, glbKey]);

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
  const stepIndex = Math.max(1, STEPS.indexOf(state.screen) + 1);

  return (
    <div className="container">
      <header className="masthead">
        <h1>Apartment Intelligence</h1>
      </header>

      {state.screen === "locate" && <h2 className="question">Will this apartment get the sun you expect?</h2>}
      {state.screen === "place" && <h2 className="question">Choose the wing and layout you recognise.</h2>}
      {state.screen === "confirm" && <h2 className="question">Confirm the placement you see.</h2>}
      {state.screen === "analysis" && <h2 className="question">Sun, shade and radiation on your floor.</h2>}
      {state.screen === "export" && <h2 className="question">Keep the evidence.</h2>}

      <div className="workbench">
        <div className="canvas-col">
          <div className="canvas" ref={canvasRef} role="img" aria-label="Three-dimensional precinct model with the target tower and the confirmed apartment">
            <span className="north" aria-label="Compass; the arrow points to true north"><svg ref={compassRef} viewBox="-22 -22 44 44"><circle r="20" fill="none" stroke="#b9b7ae" /><polygon points="0,-18 5,4 0,1 -5,4" fill="#c8472d" /><polygon points="0,18 5,-4 0,-1 -5,-4" fill="#5f665f" /><text y="-11" textAnchor="middle" fontSize="8" fill="#18211d" fontFamily="Inter, system-ui">N</text></svg></span>
            {basemap && <span className="attribution">Map data © OpenStreetMap contributors</span>}
            <span className="edge">{state.view.camera} view · Dawson precinct, ENU metres · {state.view.preset}{r ? ` · ${state.view.date} ${state.view.hour}:00` : ""}</span>
          </div>
          <div className="toolbar" aria-label="Canvas controls">
            {(["precinct", "tower", "home", "plan"] as const).map((c) => <button key={c} aria-pressed={state.view.camera === c} onClick={() => { dispatch({ type: "set_view", view: { camera: c } }); viewerRef.current?.preset(c, focus); }}>{c[0].toUpperCase() + c.slice(1)}</button>)}
            <button onClick={() => viewerRef.current?.preset("north")}>North</button>
            <button onClick={() => viewerRef.current?.preset(state.view.camera, focus)}>Reset</button>
            <button aria-pressed={basemap} onClick={() => setBasemap(!basemap)}>Map</button>
          </div>
          {r && <div className="legend" style={{ marginTop: 8 }}>
            {state.view.preset === "shadow" ? <><span style={{ width: 12, height: 12, background: "#f2c230", display: "inline-block" }} /> lit <span style={{ width: 12, height: 12, background: "#45534d", display: "inline-block" }} /> shaded</> : <><span>{state.view.preset === "radiation" ? "0" : "0 h"}</span><span className="ramp" /><span>{state.view.preset === "radiation" ? `${r.radiation.max} kWh/m² per year` : "hours of direct sun"}</span></>}
            <span style={{ marginLeft: "auto" }}>{r.sensors.count} sensors at {r.sensors.grid.spacing_m} m · plane 0.8 m</span>
          </div>}
        </div>

        <aside className="rail">
          <section className="study-card" aria-label="Study">
            <div className="study-line"><strong>{state.address}</strong>{state.studyId ? `, storey ${state.storey}` : ""}</div>
            <div className="study-meta steps" aria-live="polite">
              <button className="step-arrow" aria-label="Previous step" disabled={stepIndex <= 1} onClick={() => dispatch({ type: "go", screen: STEPS[stepIndex - 2] })}>←</button>
              <span>Step {stepIndex} of 5 · {({ locate: "Locate", place: "Place", confirm: "Confirm", analysis: "Analyse", export: "Export" } as any)[state.screen]}{state.studyState ? ` · ${STATE_WORDS[state.studyState] ?? state.studyState}` : ""}</span>
              <button className="step-arrow" aria-label="Next step" disabled={!canAdvance(state)} onClick={() => dispatch({ type: "go", screen: STEPS[stepIndex] })}>→</button>
            </div>
            <div className="study-meta">{mcp ? (mcp.registered ? `WebMCP tools registered on ${mcp.where}` : "WebMCP not enabled in this browser (chrome://flags/#enable-webmcp-testing)") : ""}</div>
          </section>
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
            <label>Your slot on storey {state.storey}</label>
            <p className="status" style={{ padding: 0 }}>Click one of the eight outlined 4-room slots on the tower, or pick it here. Which end of each wing is 4-room is not published, so both are offered.</p>
            <div className="slot-grid">{slots.map((sl) => <button key={sl.id} aria-pressed={state.placement.facade === sl.facade && state.placement.stack_position === sl.stack_position} onClick={() => dispatch({ type: "set_placement", placement: { facade: sl.facade as any, stack_position: sl.stack_position as any } })}>{sl.label}</button>)}</div>
            <label>Published layout</label>
            <div className="toolbar">{([["A", "Type A, three bedrooms"], ["B", "Type B, larger living"], ["C", "Type C, master suite"]] as const).map(([v, l]) => <button key={v} aria-pressed={state.placement.variant === v} onClick={() => dispatch({ type: "set_placement", placement: { variant: v } })}>{l}</button>)}</div>
            <label className="checks" style={{ marginTop: 8 }}><input type="checkbox" checked={state.placement.mirrored} onChange={(e) => dispatch({ type: "set_placement", placement: { mirrored: e.target.checked } })} /> Mirrored plan</label>
            <details><summary>Windows, balcony and railings (assumed unless published)</summary>
              <div className="checks" style={{ marginTop: 8 }}>{toggles.map((e: any) => <label key={e.id}><input type="checkbox" checked={state.placement.openings[e.id] ?? e.enabled_by_default} onChange={(ev) => dispatch({ type: "set_placement", placement: { openings: { [e.id]: ev.target.checked } } })} /> {labelOf(e.id)} <span style={{ color: "var(--ink-muted)", fontSize: 12 }}>{e.source.state}</span></label>)}</div>
            </details>
            <div className="toolbar">
              <button className="confirm" data-testid="confirm-button" disabled={!!state.busy || state.placementRevision === 0} onClick={(ev) => confirmFromClick(ctx, ev.isTrusted && (navigator as any).userActivation?.isActive !== false).catch(() => {})}>I confirm this is my apartment</button>
            </div>
            <p className="confirm-sentence">You are confirming the {state.placement.facade} wing, {state.placement.stack_position === "end" ? "wing-tip" : "inner"} stack, Type {state.placement.variant}{state.placement.mirrored ? ", mirrored" : ""}, on storey {state.storey}. A tool cannot do this for you.</p>
          </section>}

          {(state.screen === "analysis" || state.screen === "export") && <section>
            {!r && <div className="toolbar">
              <button className="primary" disabled={!!state.busy} onClick={() => runAnalysis(ctx, 0.25).catch(() => {})}>Run the analysis (0.25 m grid)</button>
              <button disabled={!!state.busy} onClick={() => runAnalysis(ctx, 0.5).catch(() => {})}>Fast (0.5 m)</button>
            </div>}
            {r && <>
              <label>Study</label>
              <div className="toolbar">{(["sunpath", "shadow", "solar_access", "radiation"] as const).map((p) => <button key={p} aria-pressed={state.view.preset === p} onClick={() => showAnalysis(ctx, { preset: p })}>{(p[0].toUpperCase() + p.slice(1)).replace("_", " ")}</button>)}</div>
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
              <div className="toolbar"><button className="primary" onClick={() => dispatch({ type: "go", screen: "export" })}>Keep the evidence</button></div>
            </>}
          </section>}

          {state.screen === "export" && r && <section>
            <div className="toolbar">
              {["glb", "obj", "3dm", "evidence.json", "cards.svg", "png", "pdf", "zip"].map((f) => <button key={f} onClick={() => exportFromPage([f])}>{f}</button>)}
            </div>
            <p className="status">SVG, GLB, OBJ and evidence.json are byte-stable and bound to the digest. PNG and PDF are presentation renders. 3DM embeds fresh object ids.</p>
          </section>}

          <p className={"status" + (state.message?.kind === "error" ? " error" : "")} role="status" aria-live="polite">{state.busy ? `${state.busy}…` : state.message?.text ?? ""}</p>
          {state.lastActor === "webmcp" && <p className="status">Last change came from a WebMCP tool; the page state is what you see.</p>}
        </aside>
      </div>

      {r && <section className="chapter">
        <h2>Per room</h2>
        <table className="evidence"><tbody>{Object.entries(r.radiation.per_room).map(([k, v]: any) => <tr key={k}><td>{k}</td><td>{v.sensors} sensors</td><td>min {v.min}</td><td>avg {v.avg}</td><td>max {v.max}</td></tr>)}</tbody></table>
        <details style={{ marginTop: 8 }}><summary>Explain evidence (same record a tool receives)</summary><pre style={{ fontSize: 11, whiteSpace: "pre-wrap" }}>{JSON.stringify(explainEvidence(ctx, "digest"), null, 1)}</pre></details>
      </section>}
      <footer className="colophon">
        <div className="colophon-brand">Apartment Intelligence</div>
        <div className="colophon-line">A Senibina public-interest study · Singapore first</div>
        <div className="status">Footprints and storey counts: HDB via data.gov.sg, Singapore Open Data Licence v1.0. No endorsement by HDB, OneMap or the Singapore Government. Not a valuation, compliance or daylight certification.</div>
      </footer>
    </div>
  );
}
