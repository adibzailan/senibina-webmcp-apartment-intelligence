/** WebMCP registry: nine tools on document.modelContext (navigator.modelContext fallback for
 *  Chrome < 152). No confirmation tool exists; a `confirmed` argument is rejected. */
import { surveyUnit, Ctx, createStudy, explainEvidence, proposePlacement, runAnalysis, showAnalysis } from "./actions";
import { summarise } from "./state";

type ToolDef = { name: string; description: string; inputSchema: any; annotations?: any; execute: (input: any) => Promise<any> | any };

export function toolDefinitions(ctx: Ctx, supported: any[], exportFromPage: (formats: string[]) => Promise<any>): ToolDef[] {
  const closed = (props: any, required: string[] = []) => ({ type: "object", properties: props, required, additionalProperties: false });
  const rejectConfirmed = (input: any) => {
    if (input && "confirmed" in input) throw new Error("422: `confirmed` is not an accepted argument; confirmation is a visible click in the page.");
  };
  const wrap = (fn: (i: any) => any) => async (input: any) => {
    rejectConfirmed(input);
    ctx.dispatch({ type: "actor", actor: "webmcp" });
    return fn(input ?? {});
  };
  return [
    { name: "list_supported_homes", description: "List the HDB addresses and storey ranges this build can analyse (read-only).", inputSchema: closed({}), annotations: { readOnlyHint: true }, execute: wrap(() => ({ homes: supported })) },
    { name: "create_apartment_study", description: "Start a study for an address and storey. Returns needs_confirmation; the resident must confirm in the page.", inputSchema: closed({ address: { type: "string" }, storey: { type: "integer", minimum: 1, maximum: 60 } }, ["address", "storey"]), execute: wrap((i) => createStudy(ctx, i.address, i.storey)) },
    { name: "propose_unit_placement", description: "Stage a placement (facade NE/NW/SW/SE, stack_position end/inner, variant A/B/C, mirrored). Staging only; never confirms.", inputSchema: closed({ study_id: { type: "string" }, facade: { type: "string", enum: ["NE", "NW", "SW", "SE"] }, stack_position: { type: "string", enum: ["end", "inner"] }, variant: { type: "string", enum: ["A", "B", "C"] }, mirrored: { type: "boolean" } }, ["study_id", "facade"]), execute: wrap((i) => { const { study_id, ...p } = i; if (study_id !== ctx.getState().studyId) throw new Error("404: unknown study_id"); return proposePlacement(ctx, p); }) },
    { name: "get_study_state", description: "Concise study state and provenance summary (read-only).", inputSchema: closed({ study_id: { type: "string" } }, ["study_id"]), annotations: { readOnlyHint: true }, execute: wrap((i) => { if (i.study_id !== ctx.getState().studyId) throw new Error("404: unknown study_id"); return summarise(ctx.getState()); }) },
    { name: "run_solar_analysis", description: "Run the deterministic Ladybug + Radiance analysis. Refused unless the current placement was confirmed by a visible click.", inputSchema: closed({ study_id: { type: "string" }, grid_spacing_m: { type: "number", enum: [0.1, 0.25, 0.5] } }, ["study_id"]), execute: wrap((i) => { if (i.study_id !== ctx.getState().studyId) throw new Error("404: unknown study_id"); return runAnalysis(ctx, i.grid_spacing_m ?? 0.25); }) },
    { name: "show_analysis", description: "Switch the visible view: analysis sunpath|shadow|solar_access|radiation, date MM-DD, hour, camera precinct|tower|home|plan (presentation only, read-only).", inputSchema: closed({ analysis: { type: "string", enum: ["sunpath", "shadow", "solar_access", "radiation"] }, date: { type: "string" }, hour: { type: "number" }, camera: { type: "string", enum: ["precinct", "tower", "home", "plan"] } }), annotations: { readOnlyHint: true }, execute: wrap((i) => showAnalysis(ctx, { ...(i.analysis ? { preset: i.analysis } : {}), ...(i.date ? { date: i.date } : {}), ...(i.hour !== undefined ? { hour: i.hour } : {}), ...(i.camera ? { camera: i.camera } : {}) })) },
    { name: "explain_evidence", description: "Return the provenance record for an item: radiation|weather|sunpath|shadow|solar_access|placement|provenance|digest (numbers unaltered, read-only).", inputSchema: closed({ study_id: { type: "string" }, item: { type: "string" } }, ["study_id", "item"]), annotations: { readOnlyHint: true }, execute: wrap((i) => explainEvidence(ctx, i.item)) },
    { name: "survey_unit", description: "Agent exploration: analyse a staged placement for an address, storey, facade, stack position and layout WITHOUT confirmation. Every number comes back labelled survey_unconfirmed; no study is created and no report can be made from it. Use it to compare several units, then create a study for the one the resident will confirm.", inputSchema: closed({ address: { type: "string" }, storey: { type: "integer", minimum: 1, maximum: 60 }, facade: { type: "string", enum: ["NE", "NW", "SW", "SE"] }, stack_position: { type: "string", enum: ["end", "inner"] }, variant: { type: "string", enum: ["A", "B", "C"] }, mirrored: { type: "boolean" }, grid_spacing_m: { type: "number", enum: [0.1, 0.25, 0.5] } }, ["address", "storey", "facade"]), execute: wrap((i) => surveyUnit(ctx, i)) },
    { name: "export_study", description: "Trigger downloads from the visible page for formats among glb, obj, 3dm, evidence.json, cards.svg, pdf, zip.", inputSchema: closed({ study_id: { type: "string" }, formats: { type: "array", items: { type: "string", enum: ["glb", "obj", "3dm", "evidence.json", "cards.svg", "png", "pdf", "zip"] } } }, ["study_id", "formats"]), execute: wrap((i) => exportFromPage(i.formats)) },
  ];
}

export function registerWebMcp(defs: ToolDef[]): { registered: boolean; where: string; abort: () => void } {
  const mc: any = (document as any).modelContext ?? (navigator as any).modelContext;
  const where = (document as any).modelContext ? "document.modelContext" : (navigator as any).modelContext ? "navigator.modelContext" : "none";
  const ac = new AbortController();
  if (!mc) return { registered: false, where, abort: () => ac.abort() };
  for (const d of defs) {
    try {
      mc.registerTool({ name: d.name, description: d.description, inputSchema: d.inputSchema, annotations: d.annotations, execute: async (input: any) => ({ content: [{ type: "text", text: JSON.stringify(await d.execute(input)) }] }) }, { signal: ac.signal });
    } catch (e) {
      console.warn("registerTool failed", d.name, e);
    }
  }
  return { registered: true, where, abort: () => ac.abort() };
}
