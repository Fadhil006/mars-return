import { expect, test } from "vitest";
import { cellMissing, slopeClass, SLOPE_COLORS } from "../src/map/layers";
import type { RegionBundle } from "../src/mission/types";

test("slope classes follow the legend breaks", () => {
  expect([0, 4.99, 5, 9.9, 10, 15, 19.9, 20, 45].map(slopeClass)).toEqual([0, 0, 1, 1, 2, 3, 3, 4, 4]);
  expect(SLOPE_COLORS[slopeClass(90)]).toBeDefined();
});

test("a cell is missing when masked out or without elevation", () => {
  const bundle = { mask: [[true, false], [true, true]], elevation: [[1, 2], [null, 3]] } as unknown as RegionBundle;
  expect([[0, 0], [0, 1], [1, 0], [1, 1]].map(([r, c]) => cellMissing(bundle, r, c))).toEqual([false, true, true, false]);
});
