import type { Grid, RegionBundle, RegionResponse, Status } from "./types";

export class ApiFailure extends Error {
  constructor(public status: Status, public code: string, message: string, public http: number) {
    super(message);
  }
}

export const newRequestId = () => crypto.randomUUID();

async function call<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, body === undefined ? undefined : {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
    });
  } catch {
    throw new ApiFailure("data_unavailable", "network", "The planning service could not be reached.", 0);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    throw new ApiFailure(data?.status ?? "data_unavailable", data?.error?.code ?? "bad_response",
      data?.error?.message ?? `Unexpected response (HTTP ${response.status}).`, response.status);
  }
  return data as T;
}

export const post = <T>(endpoint: "plan" | "rehearse" | "reach" | "stress" | "brief", body: unknown) =>
  call<T>(`/api/${endpoint}`, body);

export async function loadBundle(): Promise<RegionBundle> {
  const region = await call<RegionResponse>("/api/region");
  const names = ["elevation.json", "slope.json", "mask.json", "rover-traverse.json"] as const;
  const loaded = await Promise.allSettled(names.map((n) => (region.layers[n] ? call<unknown>(region.layers[n]) : Promise.reject())));
  const get = <T>(i: number) => (loaded[i].status === "fulfilled" ? (loaded[i] as PromiseFulfilledResult<T>).value : null);
  // The traverse is optional in the contract, so its absence is not a missing layer.
  const missing = names.filter((n, i) => loaded[i].status === "rejected" && n !== "rover-traverse.json") as string[];
  const imageryUrl = region.layers["imagery.webp"] ?? null;
  if (!imageryUrl) missing.push("imagery.webp");
  return {
    region,
    elevation: get<Grid<number | null>>(0),
    slope: get<Grid<number | null>>(1),
    mask: get<Grid<boolean>>(2),
    traverse: get<RegionBundle["traverse"]>(3),
    imageryUrl,
    missing,
  };
}
