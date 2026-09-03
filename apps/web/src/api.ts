export type Json = Record<string, any>;

export class ApiError extends Error {
  constructor(public status: number, public code: string, public nextAction: string) {
    super(`${code}: ${nextAction}`);
  }
}

async function call(method: string, path: string, body?: Json, headers: Record<string, string> = {}): Promise<any> {
  const r = await fetch(path, { method, credentials: "same-origin", headers: { "content-type": "application/json", ...headers }, body: body === undefined ? undefined : JSON.stringify(body) });
  const ct = r.headers.get("content-type") || "";
  const data = ct.includes("json") ? await r.json() : null;
  if (!r.ok) throw new ApiError(r.status, data?.error || `HTTP_${r.status}`, data?.next_action || "Retry.");
  return data;
}

export interface Api {
  context(): Promise<Json>;
  createStudy(address: string, storey: number): Promise<Json>;
  survey(body: Json): Promise<Json>;
  getStudy(id: string): Promise<Json>;
  putPlacement(id: string, placement: Json): Promise<Json>;
  challenge(id: string, revision: number, activation: boolean): Promise<Json>;
  confirm(id: string, revision: number, challenge: string): Promise<Json>;
  analyse(id: string, spacing: number): Promise<Json>;
  result(id: string): Promise<Json>;
}

export const liveApi: Api = {
  context: () => call("GET", "/api/context"),
  createStudy: (address, storey) => call("POST", "/api/studies", { address, storey }),
  survey: (body) => call("POST", "/api/survey", body),
  getStudy: (id) => call("GET", `/api/studies/${id}`),
  putPlacement: (id, placement) => call("PUT", `/api/studies/${id}/placement`, placement),
  challenge: (id, revision, activation) => call("POST", `/api/studies/${id}/confirmation-challenge`, { placement_revision: revision }, activation ? { "X-User-Activation": "trusted" } : {}),
  confirm: (id, revision, challenge) => call("POST", `/api/studies/${id}/confirmation`, { placement_revision: revision, challenge }),
  analyse: (id, spacing) => call("POST", `/api/studies/${id}/analysis`, { grid_spacing_m: spacing }),
  result: (id) => call("GET", `/api/studies/${id}/result`),
};

export function exportUrl(id: string, name: string) {
  return `/api/studies/${id}/export/${name}`;
}
