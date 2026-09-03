import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { exportUrl, liveApi } from "./api";
import { confirmFromClick, createStudy, proposePlacement, runAnalysis, showAnalysis, explainEvidence } from "./actions";
import { cardsPdf, download, svgToPng, zipBlob } from "./cards";
import { initialState, reducer, State } from "./state";
import { Viewer } from "./viewer";
import { plateSlots } from "./slots";
import { PROJECTS } from "./projects";
import { registerWebMcp, toolDefinitions } from "./webmcp";

const STEPS: State["screen"][] = ["locate", "place", "confirm", "analysis", "export"];
const DATES = ["03-21", "06-21", "09-22", "12-21"];
const STATE_WORDS: Record<string, string> = { created: "started", placed: "placement staged", needs_confirmation: "awaiting your confirmation", ready: "confirmed, ready to analyse", analysing: "analysing", analysed: "analysed" };
const ELEMENT_LABELS: Record<string, string> = { "win-mainbed": "Main bedroom window", "win-bed2": "Bedroom 2 window", "win-bed3": "Bedroom 3 window", "win-living": "Living room window", "win-living-side": "Living room side window", "win-mainbed-side": "Main bedroom side window", "win-kitchen": "Kitchen window", "railing-serviceyard": "Service yard railing", "balcony-living": "Living room balcony", "railing-balcony": "Balcony railing" };
const labelOf = (id: string) => ELEMENT_LABELS[id] ?? id.replace(/[-_]/g, " ");
const ROOM_LABELS: Record<string, string> = { main_bedroom: "Main bedroom", bedroom_2: "Bedroom 2", bedroom_3: "Bedroom 3", living_dining: "Living and dining", corridor: "Corridor", bath_1: "Bathroom 1", bath_2: "Bathroom 2", kitchen: "Kitchen", service_yard: "Service yard", entrance: "Entrance", shelter: "Household shelter", ac_ledge: "AC ledge" };
const STATE_PLAIN: Record<string, string> = { sourced: "from public data", inferred: "estimated from public data", reconstructed: "traced from a published drawing", assumed: "an assumption you can change", computed: "computed", resident_confirmed: "confirmed by you" };
const roomOf = (id: string) => ROOM_LABELS[id] ?? id.replace(/_/g, " ");

function finding(r: any): string {
  const rooms = Object.entries(r.radiation.per_room as Record<string, any>).filter(([k]) => !["corridor", "entrance"].includes(k));
  const sorted = [...rooms].sort((a, b) => b[1].avg - a[1].avg);
  const top = sorted[0], none = rooms.filter(([, v]) => v.max === 0).map(([k]) => roomOf(k));
  const sunny = top ? `${roomOf(top[0])} receives the most sunlight over a year, about ${Math.round(top[1].avg)} kWh per square metre on average at table height.` : "";
  const dark = none.length ? ` ${none.join(", ")} ${none.length > 1 ? "receive" : "receives"} no direct sky at all, because ${none.length > 1 ? "they face" : "it faces"} into the block.` : "";
  return sunny + dark;
}

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
  const [hoverShot, setHoverShot] = useState<string | null>(null);
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

  const home = (context?.supported ?? []).find((h: any) => h.address === state.address || h.postal_code === state.address.trim());
  return (
    <div className="container">
      <header className="masthead">
        <h1>Apartment Intelligence</h1>
        {mcp && <span className={"mcp-label" + (mcp.registered ? " on" : "")} title={mcp.registered ? `Eight tools on ${mcp.where}` : "Enable chrome://flags/#enable-webmcp-testing in Chrome 152"}>{mcp.registered ? "WebMCP tools registered" : "WebMCP off in this browser"}</span>}
      </header>

      {state.screen === "locate" && <h2 className="question">Will this apartment get the sun you expect?</h2>}
      {state.screen === "locate" && <section className="projects" aria-label="Developments">
        <div className="project-grid">
          {PROJECTS.map((p) => <button key={p.slug} className={"project" + (p.live ? " live" : "")} disabled={!p.live} aria-pressed={p.live && state.address === p.address}
            onMouseEnter={() => { if (p.live && viewerRef.current) setHoverShot(viewerRef.current.snapshot()); }} onMouseLeave={() => setHoverShot(null)}
            onClick={() => { if (!p.live) return; dispatch({ type: "set_address", address: p.address! }); canvasRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }}>
            <span className="project-art" style={{ backgroundImage: p.live && hoverShot ? `url(${hoverShot})` : `url(/projects/${p.slug}.png)` }} aria-hidden="true" />
            <span className="project-name">{p.name}</span>
            <span className="project-meta">{p.town} · blocks {p.blocks} · {p.storeys} storeys</span>
            <span className="project-state">{p.live ? "Ready" : "Not yet covered"}</span>
          </button>)}
        </div>
      </section>}
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
          <div className="toolbar view-controls" aria-label="Canvas controls">
            <span className="control-group" role="group" aria-label="Look at">
              <span className="control-label">Look at</span>
              {(["precinct", "tower", "home", "plan"] as const).filter((c) => c !== "home" || state.placementRevision > 0).map((c) => <button key={c} aria-pressed={state.view.camera === c} onClick={() => { dispatch({ type: "set_view", view: { camera: c } }); viewerRef.current?.preset(c, focus); }}>{({ precinct: "Precinct", tower: "Tower", home: "Apartment", plan: "From above" } as any)[c]}</button>)}
            </span>
            <span className="control-group" role="group" aria-label="View">
              <span className="control-label">View</span>
              <button onClick={() => viewerRef.current?.preset("north")}>Face north</button>
              <button onClick={() => viewerRef.current?.preset(state.view.camera, focus)}>Reset</button>
              <button aria-pressed={basemap} onClick={() => setBasemap(!basemap)}>Map</button>
            </span>
          </div>
          {r && <div className="legend" style={{ marginTop: 8 }}>
            {state.view.preset === "shadow" ? <><span style={{ width: 12, height: 12, background: "#f2c230", display: "inline-block" }} /> lit <span style={{ width: 12, height: 12, background: "#45534d", display: "inline-block" }} /> shaded</> : <><span>{state.view.preset === "radiation" ? "0" : "0 h"}</span><span className="ramp" /><span>{state.view.preset === "radiation" ? `${r.radiation.max} kWh/m² per year` : "hours of direct sun"}</span></>}
            <span style={{ marginLeft: "auto" }}>{r.sensors.count} sensors at {r.sensors.grid.spacing_m} m · plane 0.8 m</span>
          </div>}
        </div>

        <aside className="rail">
          <section className="study-card" aria-label="Study">
            <div className="study-line"><strong>{home?.development ?? state.address}</strong></div>
            <div className="study-sub">{home ? `Block ${home.block}` : ""}{state.studyId ? (home ? `, Storey ${state.storey}` : `Storey ${state.storey}`) : ""}</div>
            <div className="study-meta steps" aria-live="polite">
              <button className="step-arrow" aria-label="Previous step" disabled={stepIndex <= 1} onClick={() => dispatch({ type: "go", screen: STEPS[stepIndex - 2] })}>←</button>
              <span>Step {stepIndex} of 5</span>
              <button className="step-arrow" aria-label="Next step" disabled={!canAdvance(state)} onClick={() => dispatch({ type: "go", screen: STEPS[stepIndex] })}>→</button>
              <span className="step-name">{({ locate: "Locate", place: "Place", confirm: "Confirm", analysis: "Analyse", export: "Export" } as any)[state.screen]}{state.studyState ? `, ${STATE_WORDS[state.studyState] ?? state.studyState}` : ""}</span>
            </div>
          </section>
          {state.screen === "locate" && <section>
            <label htmlFor="address">Address or postal code</label>
            <div className="field"><input id="address" list="homes" value={state.address} onChange={(e) => dispatch({ type: "set_address", address: e.target.value })} /></div>
            <datalist id="homes">{(context?.supported ?? []).map((h: any) => <option key={h.postal_code} value={h.address} />)}</datalist>
            <label htmlFor="storey">Storey</label>
            <div className="field"><input id="storey" type="number" min={2} max={47} value={state.storey} onChange={(e) => dispatch({ type: "set_storey", storey: Number(e.target.value) })} /></div>
            <button className="primary" disabled={!!state.busy} onClick={() => createStudy(ctx, state.address, state.storey).catch(() => {})}>Start the study</button>
            <table className="evidence coverage"><tbody>
              <tr><td>Development</td><td>SkyVille @ Dawson, Block 87</td></tr>
              <tr><td>Postal code</td><td>141087</td></tr>
              <tr><td>Storeys</td><td>2 to 47 (sky gardens at 3, 14, 25, 36)</td></tr>
              <tr><td>Plans</td><td>4-room Type A, B, C, from the published brochure</td></tr>
              <tr><td>Upper floors</td><td>Estimated from the ground outline; no storey-30 plan is published</td></tr>
            </tbody></table>
          </section>}

          {(state.screen === "place" || state.screen === "confirm") && <section>
            <label>Your slot on Storey {state.storey}</label>
            <p className="status" style={{ padding: 0 }}>Click one of the eight outlined 4-room slots on the tower, or pick it here. Which end of each wing is 4-room is not published, so both are offered.</p>
            <div className="slot-grid">{slots.map((sl) => <button key={sl.id} aria-pressed={state.placement.facade === sl.facade && state.placement.stack_position === sl.stack_position} onClick={() => dispatch({ type: "set_placement", placement: { facade: sl.facade as any, stack_position: sl.stack_position as any } })}>{sl.label}</button>)}</div>
            <label>Published layout</label>
            <div className="toolbar">{([["A", "Type A, Three Bedrooms"], ["B", "Type B, Larger Living"], ["C", "Type C, Master Suite"]] as const).map(([v, l]) => <button key={v} aria-pressed={state.placement.variant === v} onClick={() => dispatch({ type: "set_placement", placement: { variant: v } })}>{l}</button>)}</div>
            <label>Mirrored plan</label>
            <div className="toolbar"><button aria-pressed={state.placement.mirrored} onClick={() => dispatch({ type: "set_placement", placement: { mirrored: !state.placement.mirrored } })}>{state.placement.mirrored ? "Mirrored" : "As Published"}</button></div>
            <details><summary>Windows, balcony and railings (assumed unless published)</summary>
              <div className="checks" style={{ marginTop: 8 }}>{toggles.map((e: any) => <label key={e.id}><input type="checkbox" checked={state.placement.openings[e.id] ?? e.enabled_by_default} onChange={(ev) => dispatch({ type: "set_placement", placement: { openings: { [e.id]: ev.target.checked } } })} /> {labelOf(e.id)} <span style={{ color: "var(--ink-muted)", fontSize: 12 }}>{e.source.state}</span></label>)}</div>
            </details>
            <div className="toolbar">
              <button className="confirm" data-testid="confirm-button" disabled={!!state.busy || state.placementRevision === 0} onClick={(ev) => confirmFromClick(ctx, ev.isTrusted && (navigator as any).userActivation?.isActive !== false).catch(() => {})}>I confirm this is my apartment</button>
            </div>
            <p className="confirm-sentence">You are confirming the {state.placement.facade} Wing, {state.placement.stack_position === "end" ? "Wing Tip" : "Near the Core"}, Type {state.placement.variant}{state.placement.mirrored ? ", mirrored" : ""}, on Storey {state.storey}. A tool cannot do this for you.</p>
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
              <p className="status">Sunlight over a typical year, in kWh per square metre, measured at table height. Details are under the table below.</p>
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
        <h2>Room by room</h2>
        <p className="lede">{finding(r)}</p>
        <table className="evidence rooms"><thead><tr><th>Room</th><th>Points measured</th><th>Least</th><th>Average</th><th>Most</th></tr></thead><tbody>
          {Object.entries(r.radiation.per_room).sort((a: any, b: any) => b[1].avg - a[1].avg).map(([k, v]: any) => <tr key={k}><td>{roomOf(k)}</td><td>{v.sensors}</td><td>{v.min.toFixed(0)}</td><td>{v.avg.toFixed(0)}</td><td>{v.max.toFixed(0)}</td></tr>)}
        </tbody></table>
        <p className="status">kWh per square metre over a typical year, on a surface 0.8 m above the floor, {r.sensors.count} points at {r.sensors.grid.spacing_m} m spacing.</p>
      </section>}

      {r && <section className="chapter">
        <details>
          <summary>Method, sources and limitations</summary>
          <h3>What the analysis used</h3>
          <table className="evidence"><tbody>
            <tr><td>Weather</td><td>A typical year for Singapore Changi airport built from 2011–2025 records ({r.weather.period}); {r.weather.annual_ghi_kwh_m2.toFixed(0)} kWh/m² falls on open ground in that year.</td></tr>
            <tr><td>Sky model</td><td>The sky is split into {r.sky.patches} patches and each patch's yearly sunlight is computed by Radiance, the same engine architects use.</td></tr>
            <tr><td>Blocking</td><td>Every wall, floor, column and neighbouring block that can block the sky is included; light bouncing off surfaces is not.</td></tr>
            <tr><td>Measuring points</td><td>{r.sensors.count} points on a {r.sensors.grid.spacing_m} m grid, {r.sensors.grid.offset_m} m above the floor, inside the rooms.</td></tr>
          </tbody></table>
          <h3>What is known and what is assumed</h3>
          <table className="evidence"><tbody>
            {r.provenance.map((p: any, i: number) => <tr key={i}><td>{p.method}</td><td>{STATE_PLAIN[p.state] ?? p.state}</td><td>{p.limitation ?? ""}</td></tr>)}
          </tbody></table>
          <h3>Limits to keep in mind</h3>
          <ul className="limits">{r.radiation.limitations.map((l: string, i: number) => <li key={i}>{l}</li>)}</ul>
          <p className="status">Record: method {r.method_version}, result digest {r.digest.slice(0, 16)}, weather file {r.weather.sha256.slice(0, 16)}. The same record is what an agent receives from the explain_evidence tool and what every export carries.</p>
        </details>
      </section>}

      <footer className="colophon">
        <div className="colophon-brand">Apartment Intelligence</div>
        <div className="colophon-line">A public-interest study by <a className="colophon-link" href="https://senibina.com.sg" target="_blank" rel="noopener noreferrer">Senibina</a>. Singapore now, the region next.</div>
        <div className="status">Footprints and storey counts: HDB via data.gov.sg, Singapore Open Data Licence v1.0. No endorsement by HDB, OneMap or the Singapore Government. Not a valuation, compliance or daylight certification.</div>
      </footer>
    </div>
  );
}
