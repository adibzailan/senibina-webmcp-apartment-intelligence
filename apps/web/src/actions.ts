/** Actions used by BOTH the visible controls and the WebMCP tools. Confirmation is NOT here:
 *  it lives in confirmFromClick() and requires a real click (user activation) in the page. */
import { Api, ApiError } from "./api";
import { Action, Placement, State } from "./state";

export type Dispatch = (a: Action) => void;
export interface Ctx { api: Api; dispatch: Dispatch; getState: () => State }

async function guard<T>(ctx: Ctx, label: string, fn: () => Promise<T>): Promise<T> {
  ctx.dispatch({ type: "busy", busy: label });
  try {
    const out = await fn();
    ctx.dispatch({ type: "message", message: null });
    return out;
  } catch (e: any) {
    const text = e instanceof ApiError ? `${e.code}: ${e.nextAction}` : String(e?.message || e);
    ctx.dispatch({ type: "message", message: { kind: "error", text } });
    throw e;
  } finally {
    ctx.dispatch({ type: "busy", busy: null });
  }
}

export async function createStudy(ctx: Ctx, address: string, storey: number) {
  ctx.dispatch({ type: "set_address", address });
  ctx.dispatch({ type: "set_storey", storey });
  return guard(ctx, "Creating study", async () => {
    const r = await ctx.api.createStudy(address, storey);
    ctx.dispatch({ type: "study_created", studyId: r.study_id, studyState: r.state });
    return { study_id: r.study_id, state: r.state, next_action: "Propose a placement, then confirm it with a visible click in the page." };
  });
}

export async function proposePlacement(ctx: Ctx, patch: Partial<Placement>) {
  const s = ctx.getState();
  if (!s.studyId) throw new Error("No study yet; create one first.");
  ctx.dispatch({ type: "set_placement", placement: patch });
  const placement = ctx.getState().placement;
  return guard(ctx, "Staging placement", async () => {
    const r = await ctx.api.putPlacement(s.studyId!, placement);
    ctx.dispatch({ type: "placement_staged", revision: r.placement_revision, studyState: r.state });
    return { state: r.state, placement_revision: r.placement_revision, placement, next_action: "Confirm with the visible button; a tool cannot confirm." };
  });
}

/** Only called from the click handler of the visible confirm button. */
export async function confirmFromClick(ctx: Ctx, activation: boolean) {
  const s = ctx.getState();
  if (!s.studyId) throw new Error("No study.");
  return guard(ctx, "Confirming", async () => {
    const ch = await ctx.api.challenge(s.studyId!, s.placementRevision, activation);
    const r = await ctx.api.confirm(s.studyId!, s.placementRevision, ch.challenge);
    ctx.dispatch({ type: "confirmed", revision: r.confirmed_revision, studyState: r.state });
    return r;
  });
}

export async function runAnalysis(ctx: Ctx, spacing: 0.25 | 0.5 = 0.25) {
  const s = ctx.getState();
  if (!s.studyId) throw new Error("No study.");
  if (s.confirmedRevision === null || s.confirmedRevision !== s.placementRevision) {
    const msg = s.confirmedRevision === null ? "CONFIRMATION_REQUIRED: confirm the placement with the visible button first." : "STALE_CONFIRMATION: the placement changed after confirmation; confirm again.";
    ctx.dispatch({ type: "message", message: { kind: "error", text: msg } });
    return { refused: true, reason: msg };
  }
  return guard(ctx, "Running Ladybug + Radiance analysis", async () => {
    const r = await ctx.api.analyse(s.studyId!, spacing);
    const result = await ctx.api.result(s.studyId!);
    ctx.dispatch({ type: "analysed", result, digest: r.digest, studyState: r.state });
    return { state: r.state, digest: r.digest, timing_s: r.timing_s, radiation: { min: result.radiation.min, avg: result.radiation.avg, max: result.radiation.max, unit: result.radiation.unit } };
  });
}

export function showAnalysis(ctx: Ctx, view: Partial<State["view"]>) {
  ctx.dispatch({ type: "set_view", view });
  const s = ctx.getState();
  if (s.confirmedRevision !== null && s.confirmedRevision === s.placementRevision) ctx.dispatch({ type: "go", screen: "analysis" });
  return { view: ctx.getState().view, screen: ctx.getState().screen, note: s.confirmedRevision === s.placementRevision ? undefined : "Placement not confirmed; view changed but the page stays on the current step." };
}

export function explainEvidence(ctx: Ctx, item: string) {
  const r = ctx.getState().result;
  if (!r) return { error: "EXPORT_NOT_READY", next_action: "Run the analysis first." };
  const items: Record<string, any> = {
    radiation: { value: r.radiation.avg, min: r.radiation.min, max: r.radiation.max, unit: r.radiation.unit, per_room: r.radiation.per_room, method: r.method_version, engine: r.engine, sky: r.sky, limitations: r.radiation.limitations },
    weather: r.weather,
    sunpath: { method: r.sunpath.method, arcs: r.sunpath.arcs.map((a: any) => ({ date: a.date, points: a.points.length })) },
    shadow: r.shadow.instants.map((i: any) => ({ month: i.month, day: i.day, hour: i.hour, altitude_deg: i.altitude_deg, azimuth_deg: i.azimuth_deg, lit_fraction: i.lit_fraction })),
    solar_access: Object.fromEntries(Object.entries(r.solar_access).map(([d, v]: any) => [d, { max_hours: Math.max(...v.sun_hours), avg_hours: v.sun_hours.reduce((a: number, b: number) => a + b, 0) / v.sun_hours.length }])),
    placement: { placement: r.placement, recipes: r.recipes, recipe_digest: r.recipe_digest },
    provenance: r.provenance,
    digest: { digest: r.digest, method_version: r.method_version, weather_sha256: r.weather.sha256 },
  };
  return items[item] ?? { error: "UNKNOWN_ITEM", options: Object.keys(items) };
}
