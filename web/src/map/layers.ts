import type { ReachResponse, RegionBundle } from "../mission/types";

export type GridLayer = "slope" | "missing" | "envelope";

/** Slope class breaks in degrees and their colours, low to high (design 13.3). Used by the legend too. */
export const SLOPE_BREAKS = [5, 10, 15, 20] as const;
export const SLOPE_COLORS = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"] as const;

/** Index into SLOPE_COLORS: a value equal to a break belongs to the class above it. */
export const slopeClass = (deg: number) => SLOPE_BREAKS.filter((b) => deg >= b).length;

/** True for a cell with no usable terrain: masked out, or no elevation. */
export const cellMissing = (bundle: RegionBundle, r: number, c: number) =>
  bundle.mask?.[r]?.[c] === false || (!!bundle.elevation && bundle.elevation[r]?.[c] == null);

/**
 * Paints one grid layer, north up, one grid cell = `scale` pixels, transparent where the layer has nothing to say.
 * slope: class colour per valid cell. missing: hatch where mask is false or elevation is null.
 * envelope: cells with returnMin <= allowanceMin. Returns null when the data for the layer is absent.
 */
export function layerCanvas(kind: GridLayer, bundle: RegionBundle, reach?: ReachResponse | null, scale = 4): HTMLCanvasElement | null {
  const { width, height } = bundle.region.manifest;
  if (kind === "slope" ? !bundle.slope : kind === "envelope" ? !reach : !bundle.mask && !bundle.elevation) return null;
  const canvas = document.createElement("canvas");
  canvas.width = width * scale;
  canvas.height = height * scale;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  for (let r = 0; r < height; r++) {
    for (let c = 0; c < width; c++) {
      if (kind === "slope") {
        const deg = bundle.slope![r]?.[c];
        if (deg == null) continue;
        ctx.fillStyle = SLOPE_COLORS[slopeClass(deg)];
      } else if (kind === "envelope") {
        const min = reach!.returnMin[r]?.[c];
        if (min == null || min > reach!.allowanceMin) continue;
        ctx.fillStyle = "rgba(61, 214, 232, 0.35)";
      } else {
        if (!cellMissing(bundle, r, c)) continue;
        // "/" stripes in canvas pixels: the opposite direction to the corridor's "\" hatch.
        ctx.fillStyle = "#7a858f";
        for (let y = r * scale; y < (r + 1) * scale; y++)
          for (let x = c * scale; x < (c + 1) * scale; x++)
            if ((x + y) % 6 < 2) ctx.fillRect(x, y, 1, 1);
        continue;
      }
      ctx.fillRect(c * scale, r * scale, scale, scale);
    }
  }
  return canvas;
}
