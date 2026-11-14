// Pure geometry for the 3D view. No three.js or DOM here, so it is unit-tested directly.
import { cellCenter, elevationAt, extentM } from "../mission/geo";
import type { Grid, RegionBundle, XY } from "../mission/types";

export type Vec3 = [number, number, number];

/** The one conversion every mark uses: east → X, north → −Z, elevation above the stored origin → Y. Metres, vertical scale 1. */
export const toScene = ([x, y]: XY, elevationM: number, originElevM: number): Vec3 => [x, elevationM - originElevM, -y];

/** Stored origin elevation: the lowest valid cell. */
export function originElevation(elevation: Grid<number | null>): number {
  let min = Infinity;
  for (const row of elevation) for (const v of row) if (v != null && v < min) min = v;
  return Number.isFinite(min) ? min : 0;
}

/** A point on the surface lifted by a display-only offset, or null where there is no elevation. */
export function surfacePoint(bundle: RegionBundle, xy: XY, originElevM: number, liftM = 0): Vec3 | null {
  const e = elevationAt(bundle, xy);
  return e == null ? null : toScene(xy, e + liftM, originElevM);
}

/** Two upward-facing triangles per grid quad; any triangle touching a missing vertex is omitted, never bridged. */
export function meshIndices(valid: boolean[][]): number[] {
  const rows = valid.length, cols = valid[0]?.length ?? 0, out: number[] = [];
  for (let r = 0; r + 1 < rows; r++) for (let c = 0; c + 1 < cols; c++) {
    const a = r * cols + c, b = a + 1, d = a + cols, e = d + 1; // NW, NE, SW, SE
    if (valid[r][c] && valid[r + 1][c] && valid[r][c + 1]) out.push(a, d, b);
    if (valid[r][c + 1] && valid[r + 1][c] && valid[r + 1][c + 1]) out.push(b, d, e);
  }
  return out;
}

/** One vertex per grid cell centre, thinned by a whole stride only when a side exceeds `cap` vertices. */
export function heightfield(bundle: RegionBundle, cap = 256) {
  const m = bundle.region.manifest, elevation = bundle.elevation!, { w, h } = extentM(m);
  const step = Math.ceil(Math.max(m.width, m.height) / cap);
  const origin = originElevation(elevation);
  const positions: number[] = [], uvs: number[] = [], valid: boolean[][] = [];
  for (let row = 0; row < m.height; row += step) {
    const line: boolean[] = [];
    for (let col = 0; col < m.width; col += step) {
      const e = elevation[row][col], ok = e != null && (bundle.mask ? bundle.mask[row][col] : true);
      const xy = cellCenter(m, row, col);
      positions.push(...toScene(xy, ok ? e : origin, origin));
      uvs.push((xy[0] - m.originXY[0]) / w, (xy[1] - m.originXY[1]) / h); // v = 1 is north, matching the north-up image
      line.push(ok);
    }
    valid.push(line);
  }
  return { positions, uvs, indices: meshIndices(valid), origin, rows: valid.length, cols: valid[0]?.length ?? 0, valid };
}

/**
 * Vertical side walls along the four edges of the heightfield, from each edge vertex's real height down to `baseY`.
 * Display only: the top edge of every wall is the measured edge profile; a wall segment touching a missing vertex is
 * omitted, so a gap at the edge stays a gap. Returns flat triangle positions (no index), outward-facing.
 */
export function skirtPositions(field: { positions: number[]; rows: number; cols: number; valid: boolean[][] }, baseY: number): number[] {
  const { positions, rows, cols, valid } = field, out: number[] = [];
  const at = (r: number, c: number): Vec3 => { const i = (r * cols + c) * 3; return [positions[i], positions[i + 1], positions[i + 2]]; };
  // The outermost row/column holding any valid vertex: border cells are often masked (slope needs a full 3 × 3
  // neighbourhood), so the walls follow the mesh's real edge rather than the empty grid border.
  const rowHas = (r: number) => valid[r].some(Boolean), colHas = (c: number) => valid.some((row) => row[c]);
  const top = Array.from({ length: rows }, (_, r) => r).find(rowHas), bottom = Array.from({ length: rows }, (_, r) => rows - 1 - r).find(rowHas);
  const left = Array.from({ length: cols }, (_, c) => c).find(colHas), right = Array.from({ length: cols }, (_, c) => cols - 1 - c).find(colHas);
  if (top == null || bottom == null || left == null || right == null) return out;
  const span = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, k) => a + k);
  const edges: [number, number][][] = [
    span(left, right).reverse().map((c) => [top, c]), // north edge
    span(top, bottom).map((r) => [r, left]), // west edge
    span(left, right).map((c) => [bottom, c]), // south edge
    span(top, bottom).reverse().map((r) => [r, right]), // east edge
  ];
  for (const edge of edges) for (let k = 0; k + 1 < edge.length; k++) {
    const [r1, c1] = edge[k], [r2, c2] = edge[k + 1];
    if (!valid[r1][c1] || !valid[r2][c2]) continue;
    const a = at(r1, c1), b = at(r2, c2);
    const a0: Vec3 = [a[0], baseY, a[2]], b0: Vec3 = [b[0], baseY, b[2]];
    out.push(...a, ...a0, ...b, ...b, ...a0, ...b0);
  }
  return out;
}
