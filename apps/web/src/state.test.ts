import { describe, expect, it } from "vitest";
import { Api } from "./api";
import { createStudy, proposePlacement, runAnalysis, showAnalysis } from "./actions";
import { initialState, reducer, State } from "./state";
import { toolDefinitions } from "./webmcp";

function fakeApi(): Api {
  let rev = 0;
  return {
    context: async () => ({}),
    createStudy: async () => ({ study_id: "s1", state: "created" }),
    getStudy: async () => ({}),
    putPlacement: async () => ({ state: "needs_confirmation", placement_revision: ++rev }),
    challenge: async (_id, _r, activation) => { if (!activation) throw new Error("403"); return { challenge: "c" }; },
    confirm: async (_id, r) => ({ state: "ready", confirmed_revision: r }),
    analyse: async () => ({ state: "analysed", digest: "abc", timing_s: 1 }),
    result: async () => ({ radiation: { min: 0, avg: 1, max: 2, unit: "kWh/m2", per_room: {} }, digest: "abc" }),
  };
}

function harness() {
  let state: State = initialState;
  const ctx = { api: fakeApi(), dispatch: (a: any) => { state = reducer(state, a); }, getState: () => state };
  return { ctx, get: () => state };
}

describe("UI and WebMCP drive the same reducer", () => {
  it("tool sequence equals click sequence", async () => {
    const ui = harness();
    await createStudy(ui.ctx, "87 Dawson Road", 30);
    await proposePlacement(ui.ctx, { facade: "SE", variant: "B" });
    showAnalysis(ui.ctx, { preset: "shadow" });

    const mcp = harness();
    const tools = Object.fromEntries(toolDefinitions(mcp.ctx, [], async () => ({})).map((t) => [t.name, t]));
    await tools.create_apartment_study.execute({ address: "87 Dawson Road", storey: 30 });
    await tools.propose_unit_placement.execute({ study_id: "s1", facade: "SE", variant: "B" });
    await tools.show_analysis.execute({ analysis: "shadow" });

    const strip = (s: State) => ({ ...s, lastActor: null });
    expect(strip(mcp.get())).toEqual(strip(ui.get()));
    expect(mcp.get().screen).toBe("confirm"); // show_analysis never skips confirmation
  });

  it("run_solar_analysis is refused before confirmation and has no confirm tool", async () => {
    const h = harness();
    const defs = toolDefinitions(h.ctx, [], async () => ({}));
    expect(defs.map((d) => d.name).sort()).toEqual(["create_apartment_study", "explain_evidence", "export_study", "get_study_state", "list_supported_homes", "propose_unit_placement", "run_solar_analysis", "show_analysis"]);
    expect(defs.some((d) => /confirm/.test(d.name))).toBe(false);
    const tools = Object.fromEntries(defs.map((t) => [t.name, t]));
    await tools.create_apartment_study.execute({ address: "87 Dawson Road", storey: 30 });
    await tools.propose_unit_placement.execute({ study_id: "s1", facade: "NE" });
    const r = await tools.run_solar_analysis.execute({ study_id: "s1" });
    expect(r.refused).toBe(true);
    await expect(tools.propose_unit_placement.execute({ study_id: "s1", facade: "NE", confirmed: true })).rejects.toThrow(/422/);
  });

  it("read tools carry readOnlyHint", () => {
    const h = harness();
    const ro = toolDefinitions(h.ctx, [], async () => ({})).filter((d) => d.annotations?.readOnlyHint).map((d) => d.name).sort();
    expect(ro).toEqual(["explain_evidence", "get_study_state", "list_supported_homes", "show_analysis"]);
  });

  it("stale confirmation after re-placement refuses analysis", async () => {
    const h = harness();
    await createStudy(h.ctx, "87 Dawson Road", 30);
    await proposePlacement(h.ctx, { facade: "NE" });
    h.ctx.dispatch({ type: "confirmed", revision: 1, studyState: "ready" });
    await proposePlacement(h.ctx, { facade: "SW" });
    const r: any = await runAnalysis(h.ctx);
    expect(r.refused).toBe(true);
    expect(h.get().message?.text).toMatch(/STALE/);
  });
});
