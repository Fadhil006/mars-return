import { expect, test } from "vitest";
import { arrowsAlong, calloutSide, cellMissing, slopeClass, SLOPE_COLORS } from "../src/map/layers";
import type { RegionBundle } from "../src/mission/types";

test("slope classes follow the legend breaks", () => {
  expect([0, 4.99, 5, 9.9, 10, 15, 19.9, 20, 45].map(slopeClass)).toEqual([0, 0, 1, 1, 2, 3, 3, 4, 4]);
  expect(SLOPE_COLORS[slopeClass(90)]).toBeDefined();
});

test("a cell is missing when masked out or without elevation", () => {
  const bundle = { mask: [[true, false], [true, true]], elevation: [[1, 2], [null, 3]] } as unknown as RegionBundle;
  expect([[0, 0], [0, 1], [1, 0], [1, 1]].map(([r, c]) => cellMissing(bundle, r, c))).toEqual([false, true, true, false]);
});

test("direction arrows sit evenly along the path and point the way of travel", () => {
  const pts: [number, number][] = [[0, 0], [10, 0], [10, 10]];
  const arrows = arrowsAlong(pts, 2, 0.5); // at 5 m and 15 m of 20 m
  expect(arrows.map((a) => a.at)).toEqual([[5, 0], [10, 5]]);
  expect(arrows.map((a) => a.heading)).toEqual([0, Math.PI / 2]);
  expect(arrowsAlong([[1, 1], [1, 1]], 3)).toEqual([]);
});

test("callouts lean away from each other and back from the edges", () => {
  expect(calloutSide([0.7, 0.6], [0.3, 0.8])).toEqual({ left: true, up: true }); // flips back from the east edge
  expect(calloutSide([0.3, 0.8], [0.7, 0.6])).toEqual({ left: false, up: true }); // west edge: leans east
  expect(calloutSide([0.5, 0.1], [0.4, 0.5])).toEqual({ left: false, up: false }); // near the top: goes down
  expect(calloutSide([0.8, 0.5])).toEqual({ left: true, up: true });
});
