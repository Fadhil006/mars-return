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
 * Hypothetical blocked corridor: a square of `halfM` centred on a returned vertex still to be
 * travelled, as near the middle of the remaining return as possible while clear of the current
 * position, the target and the base (the service rejects a blocked target or base rather than
 * testing it). Null when no remaining vertex is clear of all three.
 */
export function corridorPolygon(points: RoutePoint[], posIndex: number, halfM = 60): XY[] | null {
  const last = points.length - 1, target = points.map((p) => p.leg).lastIndexOf("outbound");
  if (target < 0) return null;
  const clear = ([x, y]: XY) => [points[posIndex].xy, points[target].xy, points[last].xy]
    .every((p) => Math.max(Math.abs(p[0] - x), Math.abs(p[1] - y)) > halfM * 1.5);
  const mid = Math.floor((Math.max(posIndex, target) + last) / 2); // middle of the way home still ahead
  for (let d = 0; mid - d > posIndex || mid + d < last; d++) {
    for (const i of [mid - d, mid + d]) {
      if (i <= posIndex || i >= last || !clear(points[i].xy)) continue;
      const [x, y] = points[i].xy;
      return [[x - halfM, y - halfM], [x + halfM, y - halfM], [x + halfM, y + halfM], [x - halfM, y + halfM]];
    }
  }
  return null;
}

/** Development sample data is identified from the data itself, never from a setting. */
export const isSample = (bundle: RegionBundle) =>
  bundle.region.datasetVersion.startsWith("synthetic") ||
  bundle.region.sources.some((s) => s.sourceId.startsWith("synthetic")) ||
  bundle.region.scienceStops.some((s) => s.sourceIds.some((id) => id.startsWith("synthetic")));
