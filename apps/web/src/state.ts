/** Single reducer shared by the visible controls and the WebMCP tools. */
export type Screen = "locate" | "place" | "confirm" | "analysis" | "export";
export type Preset = "sunpath" | "shadow" | "solar_access" | "radiation";

export interface Placement { facade: "NE" | "NW" | "SW" | "SE"; stack_position: "end" | "inner"; variant: "A" | "B" | "C"; mirrored: boolean; openings: Record<string, boolean> }

export interface State {
  screen: Screen;
  address: string;
  storey: number;
  studyId: string | null;
  studyState: string | null;
  placement: Placement;
  placementRevision: number;
  confirmedRevision: number | null;
  result: any | null;
  digest: string | null;
  view: { preset: Preset; date: string; hour: number; camera: "precinct" | "tower" | "home" | "plan" };
  busy: string | null;
  message: { kind: "info" | "error"; text: string } | null;
  lastActor: "ui" | "webmcp" | null;
}

export const initialState: State = {
  screen: "locate",
  address: "87 Dawson Road",
  storey: 30,
  studyId: null,
  studyState: null,
  placement: { facade: "NE", stack_position: "end", variant: "A", mirrored: false, openings: {} },
  placementRevision: 0,
  confirmedRevision: null,
  result: null,
  digest: null,
  view: { preset: "radiation", date: "06-21", hour: 12, camera: "precinct" },
  busy: null,
  message: null,
  lastActor: null,
};

export type Action =
  | { type: "set_address"; address: string }
  | { type: "set_storey"; storey: number }
  | { type: "study_created"; studyId: string; studyState: string }
  | { type: "set_placement"; placement: Partial<Placement> }
  | { type: "placement_staged"; revision: number; studyState: string }
  | { type: "confirmed"; revision: number; studyState: string }
  | { type: "analysed"; result: any; digest: string; studyState: string }
  | { type: "set_view"; view: Partial<State["view"]> }
  | { type: "go"; screen: Screen }
  | { type: "busy"; busy: string | null }
  | { type: "message"; message: State["message"] }
  | { type: "actor"; actor: "ui" | "webmcp" }
  | { type: "reset" };

export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "set_address": return { ...s, address: a.address };
    case "set_storey": return { ...s, storey: a.storey };
    case "study_created": return { ...s, studyId: a.studyId, studyState: a.studyState, screen: "place", placementRevision: 0, confirmedRevision: null, result: null, digest: null, message: null };
    case "set_placement": return { ...s, placement: { ...s.placement, ...a.placement, openings: { ...s.placement.openings, ...(a.placement.openings || {}) } }, result: null, digest: null };
    case "placement_staged": return { ...s, placementRevision: a.revision, studyState: a.studyState, screen: "confirm", result: null, digest: null };
    case "confirmed": return { ...s, confirmedRevision: a.revision, studyState: a.studyState, screen: "analysis" };
    case "analysed": return { ...s, result: a.result, digest: a.digest, studyState: a.studyState, screen: "analysis" };
    case "set_view": return { ...s, view: { ...s.view, ...a.view } };
    case "go": return { ...s, screen: a.screen };
    case "busy": return { ...s, busy: a.busy };
    case "message": return { ...s, message: a.message };
    case "actor": return { ...s, lastActor: a.actor };
    case "reset": return { ...initialState };
  }
}

export function summarise(s: State) {
  return {
    study_id: s.studyId, state: s.studyState, screen: s.screen, address: s.address, storey: s.storey,
    placement: s.placement, placement_revision: s.placementRevision, confirmed_revision: s.confirmedRevision,
    confirmed: s.confirmedRevision !== null && s.confirmedRevision === s.placementRevision,
    result_digest: s.digest,
    radiation: s.result ? { min: s.result.radiation.min, avg: s.result.radiation.avg, max: s.result.radiation.max, unit: s.result.radiation.unit, per_room: s.result.radiation.per_room } : null,
    provenance: { footprint: "sourced", storeys: "sourced", plate_storey: "inferred", unit_plan: "published typical; placement assumed until confirmed", heights: "assumed" },
  };
}
