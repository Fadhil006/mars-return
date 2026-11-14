import { describe, expect, it } from "vitest";
import { diff } from "../src/mission/format";
import { cellCenter, corridorPolygon, isSample, routePoints, routesIdentical, xyToCell } from "../src/mission/geo";
import { initialState, reducer, type State } from "../src/mission/state";
import type { Assessment, Leg, Manifest, PlanResponse, RegionBundle, XY } from "../src/mission/types";

const manifest: Manifest = { width: 4, height: 3, cellSizeM: 10, originXY: [0, 0], datasetVersion: "v1" };

const leg = (path: XY[]): Leg => ({
  status: "ok", pathXY: path, distanceM: (path.length - 1) * 10, ascentM: 0, maxSlopeDeg: 1, meanSlopeDeg: 1,
  profile: path.map((_, i) => ({ distanceM: i * 10, elevationM: 0, slopeDeg: 1 })), travelMin: 1, message: null,
});
const line = (n: number): XY[] => Array.from({ length: n }, (_, i) => [i * 10 + 5, 5] as XY);
const assessment = (n = 20): Assessment => ({
  status: "ok", outbound: leg(line(n)), return: leg(line(n).reverse()), currentToTarget: null, targetToBase: null,
  totalDistanceM: 2 * (n - 1) * 10, travelMin: 2, dwellMin: 10, reserveMin: 20, totalRequiredMin: 32, marginMin: 148, message: null,
});
const plan = (requestId: string): PlanResponse => ({
  requestId, schemaVersion: 1, datasetVersion: "v1", modelVersion: "m", planId: `plan-${requestId}`, inputHash: "h",
  sourceIds: [], warnings: [], options: { shortest: assessment(), slope_penalized: assessment() },
});
const ok = { status: "ok", requestId: "x", data: {}, error: null } as never;

function currentState(): State {
  let s = reducer(initialState, { type: "planRequested", requestId: "a" });
  s = reducer(s, { type: "planLoaded", requestId: "a", plan: plan("a"), inputs: s.inputs });
  return { ...s, ret: ok, reach: ok, stress: ok, brief: ok, rehearsing: true };
}

describe("mission reducer", () => {
  it("ignores a late response for an older request", () => {
    let s = reducer(initialState, { type: "planRequested", requestId: "old" });
    s = reducer(s, { type: "planRequested", requestId: "new" });
    s = reducer(s, { type: "planLoaded", requestId: "old", plan: plan("old"), inputs: s.inputs });
    expect(s.freshness).toBe("requesting");
    expect(s.plan).toBeNull();
  });

  it("marks a current result outdated on any input change and clears dependent results", () => {
    const s = reducer(currentState(), { type: "setInput", key: "totalBudgetMin", value: 90 });
    expect(s.freshness).toBe("outdated");
    expect([s.ret.status, s.reach.status, s.stress.status, s.brief.status]).toEqual(["idle", "idle", "idle", "idle"]);
    expect(s.rehearsing).toBe(false);
  });

  it("keeps the plan current when only the route mode changes", () => {
    const s = reducer(currentState(), { type: "setInput", key: "mode", value: "slope_penalized" });
    expect(s.freshness).toBe("current");
    expect(s.planInputs?.mode).toBe("slope_penalized");
    expect(s.ret.status).toBe("idle");
    const outdated = reducer({ ...currentState(), freshness: "outdated" }, { type: "setInput", key: "mode", value: "slope_penalized" });
    expect(outdated.freshness).toBe("outdated");
  });

  it("removes the earlier route when a request fails", () => {
    let s = reducer(currentState(), { type: "planRequested", requestId: "b" });
    s = reducer(s, { type: "planFailed", requestId: "b", error: { status: "no_path", code: "c", message: "m" } });
    expect(s.freshness).toBe("failed");
    expect(s.plan).toBeNull();
  });

  it("flags an expired plan and requires recalculation", () => {
    let s = reducer(currentState(), { type: "childRequested", key: "brief", requestId: "q" });
    s = reducer(s, { type: "childFailed", key: "brief", requestId: "q", error: { status: "invalid_input", code: "plan_expired", message: "gone" } });
    expect(s.expired).toBe(true);
    expect(s.freshness).toBe("outdated");
  });

  it("opens the report only for a current result", () => {
    expect(reducer({ ...currentState(), freshness: "outdated" }, { type: "setReport", open: true }).reportOpen).toBe(false);
    expect(reducer(currentState(), { type: "setReport", open: true }).reportOpen).toBe(true);
  });

  it("clears scenario results when the playback position moves", () => {
    const s = reducer(currentState(), { type: "setPos", index: 3 });
    expect(s.ret.status).toBe("idle");
    expect(s.brief.status).toBe("idle");
    expect(s.stress.status).toBe("ok"); // the stress test does not depend on position
  });
});

describe("geometry", () => {
  it("round-trips cells with row 0 north and east/north bounds exclusive", () => {
    expect(xyToCell(manifest, [0, 29.9])).toEqual({ row: 0, col: 0 });
    expect(xyToCell(manifest, [0, 0])).toEqual({ row: 2, col: 0 });
    expect(xyToCell(manifest, [40, 5])).toBeNull();
    expect(xyToCell(manifest, [5, 30])).toBeNull();
    for (let row = 0; row < 3; row++) for (let col = 0; col < 4; col++)
      expect(xyToCell(manifest, cellCenter(manifest, row, col))).toEqual({ row, col });
  });

  it("orders route points outbound then return with continuous distance", () => {
    const pts = routePoints(assessment(5));
    expect(pts).toHaveLength(10);
    expect(pts[4]).toMatchObject({ leg: "outbound", alongM: 40 });
    expect(pts[5]).toMatchObject({ leg: "return", alongM: 40 });
    expect(pts[9].alongM).toBe(80);
  });

  it("places the corridor clear of the current position and the end, or not at all", () => {
    const pts = routePoints(assessment(20));
    const poly = corridorPolygon(pts, 0, 20)!;
    const xs = poly.map((p) => p[0]);
    const inside = (xy: XY) => xy[0] >= Math.min(...xs) && xy[0] <= Math.max(...xs);
    expect(inside(pts[0].xy)).toBe(false);
    expect(inside(pts[pts.length - 1].xy)).toBe(false);
    expect(inside(pts[pts.map((p) => p.leg).lastIndexOf("outbound")].xy)).toBe(false); // the target stays reachable
    expect(corridorPolygon(pts, pts.length - 3, 20)).toBeNull();
  });

  it("detects identical routes", () => {
    expect(routesIdentical(plan("a"))).toBe(true);
    const p = plan("b");
    p.options.slope_penalized = assessment(21);
    expect(routesIdentical(p)).toBe(false);
  });

  it("labels synthetic fixtures as sample data from the data itself", () => {
    const bundle = (datasetVersion: string, ids: string[]) => ({
      region: { datasetVersion, sources: [], scienceStops: [{ id: "s", positionXY: [0, 0], sourceIds: ids }] },
    }) as unknown as RegionBundle;
    expect(isSample(bundle("synthetic-development-v1", []))).toBe(true);
    expect(isSample(bundle("v1", ["synthetic-not-mars"]))).toBe(true);
    expect(isSample(bundle("9a4cd252af07db1a", ["nasa-m20-waypoints"]))).toBe(false);
  });
});

describe("format", () => {
  it("signs differences between returned values", () => {
    expect(diff(100, 133)).toBe("+33");
    expect(diff(133, 100)).toBe("−33");
    expect(diff(1, 1.0001)).toBe("0");
    expect(diff(null, 1)).toBe("—");
  });
});
