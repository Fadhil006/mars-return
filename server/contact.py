"""Line of sight from the hypothetical base: geometric, on the 20 m DEM, no antenna pattern, relay or diffraction."""

import math

import numpy as np

from server.coordinates import xy_to_pixel

MARS_RADIUS_M = 3389500.0
STEP_CELLS = 0.5  # sample spacing along each sight line
_CACHE = {}


def _elevation(region):
    """Elevation as floats with NaN wherever the mask or the value says data is missing."""
    elevation = np.array([[v if isinstance(v, (int, float)) and not isinstance(v, bool) else np.nan for v in row]
                          for row in region["elevation"]], dtype=float)
    elevation[~np.array(region["mask"], dtype=bool)] = np.nan
    return elevation


def _bilinear(grid, rows, cols):
    """NaN if any of the four neighbours is missing, so a sight line across a gap counts as blocked."""
    h, w = grid.shape
    r0 = np.clip(np.floor(rows).astype(int), 0, h - 2)
    c0 = np.clip(np.floor(cols).astype(int), 0, w - 2)
    fr, fc = np.clip(rows - r0, 0, 1), np.clip(cols - c0, 0, 1)
    top = grid[r0, c0] * (1 - fc) + grid[r0, c0 + 1] * fc
    bottom = grid[r0 + 1, c0] * (1 - fc) + grid[r0 + 1, c0 + 1] * fc
    return top * (1 - fr) + bottom * fr


def viewshed(region, base_xy, mast_m=2.0, eye_m=1.7):
    """Boolean grid: True where a person standing in the cell can see the top of the base mast.

    A cell is visible when no terrain sample along the straight line between cell centres rises above the sight
    line. Terrain heights are lowered by the curvature drop d^2 / 2R relative to the base. Cells without data are
    never visible, and a sight line crossing missing data is blocked.
    """
    manifest = region["manifest"]
    key = (id(region), manifest["datasetVersion"], tuple(xy_to_pixel(*base_xy, manifest)), float(mast_m), float(eye_m))
    if key in _CACHE:
        return _CACHE[key]
    size = manifest["cellSizeM"]
    elevation = _elevation(region)
    h, w = elevation.shape
    br, bc = xy_to_pixel(*base_xy, manifest)
    if np.isnan(elevation[br, bc]):
        raise ValueError("base position has unavailable terrain data")
    observer = elevation[br, bc] + mast_m
    rows, cols = np.mgrid[0:h, 0:w]
    rows, cols = rows.ravel().astype(float), cols.ravel().astype(float)
    span = np.hypot(rows - br, cols - bc)  # cells
    target = elevation.ravel() - (span * size) ** 2 / (2 * MARS_RADIUS_M) + eye_m
    visible = ~np.isnan(target)
    samples = int(math.ceil(span.max() / STEP_CELLS))
    for start in range(0, rows.size, 2048):
        chunk = slice(start, start + 2048)
        n = span[chunk]
        t = (np.arange(1, samples + 1) * STEP_CELLS)[None, :] / np.maximum(n, 1e-9)[:, None]
        inside = t < 1 - STEP_CELLS / np.maximum(n, 1e-9)[:, None]  # stop half a cell short of the target
        sr = br + t * (rows[chunk, None] - br)
        sc = bc + t * (cols[chunk, None] - bc)
        terrain = _bilinear(elevation, sr, sc) - (t * n[:, None] * size) ** 2 / (2 * MARS_RADIUS_M)
        line = observer + t * (target[chunk, None] - observer)
        blocked = inside & (np.isnan(terrain) | (terrain > line))
        visible[chunk] &= ~blocked.any(axis=1)
    visible[br * w + bc] = True
    grid = visible.reshape(h, w)
    if len(_CACHE) > 32:
        _CACHE.clear()
    _CACHE[key] = grid
    return grid


def contact_metrics(leg, visible, manifest, speed):
    """Time out of sight along a leg. A step between two path cells is in contact only if both cells are visible."""
    path, profile = leg.get("pathXY"), leg.get("profile")
    if leg.get("status") != "ok" or not path or not profile:
        return {}
    flags = [bool(visible[r][c]) for r, c in (xy_to_pixel(x, y, manifest) for x, y in path)]
    blind_m, longest_m, longest = 0.0, 0.0, (None, None)
    run_start = None
    for i in range(1, len(path)):
        a, b = profile[i - 1]["distanceM"], profile[i]["distanceM"]
        if flags[i - 1] and flags[i]:
            run_start = None
            continue
        blind_m += b - a
        run_start = a if run_start is None else run_start
        if b - run_start > longest_m:
            longest_m, longest = b - run_start, (run_start, b)
    return {"outOfContactM": blind_m, "outOfContactMin": blind_m / speed,
            "longestOutOfContactMin": longest_m / speed,
            "longestOutOfContactStartM": longest[0], "longestOutOfContactEndM": longest[1], "inContact": flags}
