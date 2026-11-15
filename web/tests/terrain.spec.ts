import { describe, expect, it } from "vitest";
import { cellCenter, elevationAt } from "../src/mission/geo";
import type { RegionBundle } from "../src/mission/types";
import { heightfield, meshIndices, originElevation, skirtPositions, surfacePoint, toScene } from "../src/terrain/scene";

// Invented 3 × 3 grid for transform checks only; not Mars terrain.
const bundle = (elevation: (number | null)[][], mask: boolean[][] | null = null) => ({
  region: { manifest: { width: 3, height: 3, cellSizeM: 10, originXY: [100, 200], datasetVersion: "synthetic-test" } },
  elevation, mask,
}) as unknown as RegionBundle;

describe("toScene", () => {
  it("maps east to +X, north to −Z and elevation to Y at 1×", () => {
    expect(toScene([5, 7], 12, 10)).toEqual([5, 2, -7]);
    expect(toScene([5, 8], 12, 10)[2]).toBeLessThan(toScene([5, 7], 12, 10)[2]);
    expect(toScene([0, 0], 150, 100)[1] - toScene([0, 0], 120, 100)[1]).toBe(30);
  });

  it("puts a route vertex on its own cell's height", () => {
    const b = bundle([[30, 31, 32], [20, 21, 22], [10, 11, 12]]);
    const origin = originElevation(b.elevation!);
    const xy = cellCenter(b.region.manifest, 0, 2); // north-east cell
    expect(origin).toBe(10);
    expect(elevationAt(b, xy)).toBe(32);
    expect(surfacePoint(b, xy, origin)).toEqual([125, 22, -225]);
    expect(surfacePoint(b, xy, origin, 3)![1]).toBe(25);
    expect(surfacePoint(b, [0, 0], origin)).toBeNull();
  });
});

describe("block sides", () => {
  const field = (heights: number[][], valid: boolean[][]) => ({
    positions: heights.flatMap((row, r) => row.flatMap((y, c) => [c * 10, y, -r * 10])), rows: heights.length, cols: heights[0].length, valid,
  });
  const t = true, f = false;

  it("drops each edge vertex's real height straight down to the base", () => {
    const p = skirtPositions(field([[5, 6], [7, 8]], [[t, t], [t, t]]), -3);
    expect(p).toHaveLength(4 * 6 * 3); // four edges, one segment each, two triangles
    const ys = new Set(p.filter((_, i) => i % 3 === 1));
    expect([...ys].sort((a, b) => a - b)).toEqual([-3, 5, 6, 7, 8]); // only measured heights and the base
  });

  it("follows the outermost valid ring when the grid border is masked, and leaves gaps open", () => {
    const valid = [[f, f, f, f], [f, t, t, f], [f, t, t, f], [f, f, f, f]];
    const p = skirtPositions(field([[0, 0, 0, 0], [0, 1, 2, 0], [0, 3, 4, 0], [0, 0, 0, 0]], valid), -1);
    expect(p).toHaveLength(4 * 6 * 3);
    expect(new Set(p.filter((_, i) => i % 3 === 1))).toEqual(new Set([-1, 1, 2, 3, 4]));
    // South-west corner missing: of 8 edge segments, the 2 touching it are omitted (6 segments × 2 triangles × 3 vertices × 3).
    const gap = [[t, t, t], [t, t, t], [f, t, t]];
    expect(skirtPositions(field([[1, 1, 1], [1, 1, 1], [1, 1, 1]], gap), 0)).toHaveLength(6 * 6 * 3);
  });
});

describe("mesh", () => {
  it("omits every triangle that touches a missing cell", () => {
    const t = true;
    expect(meshIndices([[t, t, t], [t, t, t], [t, t, t]])).toHaveLength(24);
    const holed = meshIndices([[t, t, t], [t, false, t], [t, t, t]]);
    expect(holed).toEqual([0, 3, 1, 5, 7, 8]);
    expect(holed).not.toContain(4);
  });

  it("treats null elevation and mask false alike, with vertices in row-major north-first order", () => {
    const field = heightfield(bundle([[30, 31, 32], [20, null, 22], [10, 11, 12]]));
    expect(field.indices).not.toContain(4);
    expect(field.positions.slice(0, 3)).toEqual([105, 20, -225]); // row 0, col 0 = north-west
    expect(field.uvs.slice(0, 2)).toEqual([0.5 / 3, 2.5 / 3]);
    const masked = heightfield(bundle([[30, 31, 32], [20, 21, 22], [10, 11, 12]],
      [[true, true, true], [true, true, true], [true, true, false]]));
    expect(masked.indices).not.toContain(8);
    expect(masked.indices).toHaveLength(21);
  });
});
