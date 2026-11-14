import type { ReachResponse, RegionBundle } from "../mission/types";

export type GridLayer = "slope" | "missing" | "envelope";

/** Slope class breaks in degrees and their colours, low to high (design 13.3). Used by the legend too. */
export const SLOPE_BREAKS = [5, 10, 15, 20] as const;
export const SLOPE_COLORS = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"] as const;

/**
 * Paints one grid layer, north up, one grid cell = `scale` pixels, transparent where the layer has nothing to say.
 * slope: class colour per valid cell. missing: hatch where mask is false or elevation is null.
 * envelope: cells with returnMin <= allowanceMin. Returns null when the data for the layer is absent.
 */
export function layerCanvas(_kind: GridLayer, _bundle: RegionBundle, _reach?: ReachResponse | null, _scale = 4): HTMLCanvasElement | null {
  return null; // stub
}
