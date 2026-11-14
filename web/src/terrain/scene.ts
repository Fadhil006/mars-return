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
  return { positions, uvs, indices: meshIndices(valid), origin };
}
