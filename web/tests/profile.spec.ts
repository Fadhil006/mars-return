import { describe, expect, it } from "vitest";
import { nearestIndex, profilePoints } from "../src/mission/ElevationProfile";
import { routePoints } from "../src/mission/geo";
import type { Assessment } from "../src/mission/types";

const leg = (xs: number[], es: number[]) => ({
  status: "ok", pathXY: xs.map((x) => [x, 0]), distanceM: xs[xs.length - 1], ascentM: 0, descentM: 0, maxSlopeDeg: 0,
  profile: xs.map((d, i) => ({ distanceM: d, elevationM: es[i], slopeDeg: 0 })), travelMin: 1, message: null,
});
const a = { outbound: leg([0, 100, 250], [-2600, -2590, -2580]), return: leg([0, 150, 250], [-2580, -2595, -2600]) } as unknown as Assessment;

describe("elevation profile", () => {
  it("uses returned samples only, summed across legs, aligned with route points", () => {
    const pts = profilePoints(a);
    expect(pts.map((p) => p.d)).toEqual([0, 100, 250, 250, 400, 500]);
    expect(pts.map((p) => p.e)).toEqual([-2600, -2590, -2580, -2580, -2595, -2600]);
    expect(routePoints(a).map((p) => p.alongM)).toEqual(pts.map((p) => p.d));
  });
  it("is empty without both leg profiles", () => {
    expect(profilePoints({ ...a, return: null } as Assessment)).toEqual([]);
  });
  it("snaps to the nearest returned sample", () => {
    const pts = profilePoints(a);
    expect(nearestIndex(pts, -10)).toBe(0);
    expect(nearestIndex(pts, 160)).toBe(1);
    expect(nearestIndex(pts, 390)).toBe(4);
    expect(nearestIndex(pts, 9999)).toBe(5);
  });
});
