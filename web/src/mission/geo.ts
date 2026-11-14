// Coordinate helpers for the contract's frame: x east, y north, row 0 north, column 0 west.
import type { Assessment, Manifest, PlanResponse, RegionBundle, XY } from "./types";

export const extentM = (m: Manifest) => ({ w: m.width * m.cellSizeM, h: m.height * m.cellSizeM });

/** Containing cell, or null outside the grid (west/south inclusive, east/north exclusive). */
export function xyToCell(m: Manifest, [x, y]: XY): { row: number; col: number } | null {
  const col = Math.floor((x - m.originXY[0]) / m.cellSizeM);
  const row = m.height - 1 - Math.floor((y - m.originXY[1]) / m.cellSizeM);
  return col >= 0 && col < m.width && row >= 0 && row < m.height ? { row, col } : null;
}

export const cellCenter = (m: Manifest, row: number, col: number): XY => [
  m.originXY[0] + (col + 0.5) * m.cellSizeM,
  m.originXY[1] + (m.height - row - 0.5) * m.cellSizeM,
];

export function elevationAt(bundle: RegionBundle, xy: XY): number | null {
  const cell = xyToCell(bundle.region.manifest, xy);
  return cell && bundle.elevation ? bundle.elevation[cell.row][cell.col] : null;
}

export interface RoutePoint { xy: XY; leg: "outbound" | "return"; alongM: number }

/** Returned vertices of a round trip in travel order. alongM is the server's profile distance, summed across legs. */
export function routePoints(a: Assessment | null | undefined): RoutePoint[] {
  const out = a?.outbound, back = a?.return;
  if (!out?.pathXY || !out.profile || !back?.pathXY || !back.profile) return [];
  const offset = out.distanceM ?? 0;
  return [
    ...out.pathXY.map((xy, i) => ({ xy, leg: "outbound" as const, alongM: out.profile![i].distanceM })),
    ...back.pathXY.map((xy, i) => ({ xy, leg: "return" as const, alongM: offset + back.profile![i].distanceM })),
  ];
}

const samePath = (a: XY[] | null | undefined, b: XY[] | null | undefined) =>
  !!a && !!b && a.length === b.length && a.every((p, i) => p[0] === b[i][0] && p[1] === b[i][1]);

export const routesIdentical = (plan: PlanResponse) =>
  samePath(plan.options.shortest.outbound?.pathXY, plan.options.slope_penalized.outbound?.pathXY) &&
  samePath(plan.options.shortest.return?.pathXY, plan.options.slope_penalized.return?.pathXY);

/** True when the return leg retraces the outbound leg, so one line is drawn. */
export const returnRetraces = (a: Assessment) =>
  samePath(a.outbound?.pathXY, a.return?.pathXY ? [...a.return.pathXY].reverse() : null);

/**
 * Hypothetical blocked corridor: a square of `halfM` centred on the returned vertex midway along
 * the path still to be travelled. Null when too little path remains to place it clear of both ends.
 */
export function corridorPolygon(points: RoutePoint[], posIndex: number, halfM = 60): XY[] | null {
  const mid = Math.floor((posIndex + points.length - 1) / 2);
  if (!points.length || mid <= posIndex || mid >= points.length - 1) return null;
  const [x, y] = points[mid].xy;
  const far = (p: XY) => Math.max(Math.abs(p[0] - x), Math.abs(p[1] - y)) > halfM * 1.5;
  if (!far(points[posIndex].xy) || !far(points[points.length - 1].xy)) return null;
  return [[x - halfM, y - halfM], [x + halfM, y - halfM], [x + halfM, y + halfM], [x - halfM, y + halfM]];
}

/** Development sample data is identified from the data itself, never from a setting. */
export const isSample = (bundle: RegionBundle) =>
  bundle.region.datasetVersion.startsWith("synthetic") ||
  bundle.region.sources.some((s) => s.sourceId.startsWith("synthetic")) ||
  bundle.region.scienceStops.some((s) => s.sourceIds.some((id) => id.startsWith("synthetic")));
