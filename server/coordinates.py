"""Coordinate transforms between the regional pixel grid and local metric XY.

Contract
--------
* All public coordinates are local metres ``[x_m, y_m]``.
* ``+x`` is East, ``+y`` is North.
* Raster pixel convention: ``row = 0`` is the North edge, ``col = 0`` is the
  West edge. Pixel indices refer to cell *centres* when converted to XY.
* The manifest stores the north-up affine transform under ``grid.transform``
  (``a``..``f``, same ordering as an affine matrix):

      x = a * col + b * row + c
      y = d * col + e * row + f

The inverse affine is used for :func:`xy_to_pixel`; out-of-bounds positions
return ``None`` rather than being silently clamped.
"""

from __future__ import annotations

from typing import Any, Mapping

__all__ = [
    "ManifestError",
    "get_grid",
    "get_bounds",
    "pixel_to_xy",
    "xy_to_pixel",
    "is_xy_in_bounds",
    "cell_center_xy",
    "xy_outside_message",
]


class ManifestError(ValueError):
    """Raised when a manifest cannot drive coordinate transforms."""


def _number(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ManifestError(f"{name} must be numeric, got {value!r}") from exc
    if out != out:  # NaN
        raise ManifestError(f"{name} must not be NaN")
    return out


def get_grid(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated grid description from ``manifest``.

    Only the north-up transform form produced by :mod:`server.preprocess` is
    accepted; rotated/sheared grids are rejected explicitly.
    """

    if not isinstance(manifest, Mapping):
        raise ManifestError("manifest must be a mapping")
    grid = manifest.get("grid")
    if not isinstance(grid, Mapping):
        raise ManifestError("manifest.grid is missing")

    rows = int(grid.get("rows", 0))
    cols = int(grid.get("cols", 0))
    if rows <= 0 or cols <= 0:
        raise ManifestError("manifest.grid.rows/cols must be positive")

    transform = grid.get("transform")
    if not isinstance(transform, Mapping):
        raise ManifestError("manifest.grid.transform is missing")
    try:
        a = _number(transform["a"], "grid.transform.a")
        b = _number(transform["b"], "grid.transform.b")
        c = _number(transform["c"], "grid.transform.c")
        d = _number(transform["d"], "grid.transform.d")
        e = _number(transform["e"], "grid.transform.e")
        f = _number(transform["f"], "grid.transform.f")
    except KeyError as exc:
        raise ManifestError(f"grid.transform missing key {exc.args[0]!r}") from exc

    if abs(b) > 1e-9 or abs(d) > 1e-9:
        raise ManifestError("only north-up transforms (b=d=0) are supported")
    if a <= 0 or e >= 0:
        raise ManifestError("north-up transform requires a>0 and e<0")

    cell_size = _number(grid.get("cellSizeM", abs(a)), "grid.cellSizeM")
    if abs(cell_size - abs(a)) > 1e-6 or abs(cell_size - abs(e)) > 1e-6:
        raise ManifestError("grid.cellSizeM must match |a| and |e|")

    return {
        "rows": rows,
        "cols": cols,
        "cell_size_m": cell_size,
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "e": e,
        "f": f,
    }


def get_bounds(manifest: Mapping[str, Any]) -> dict[str, float]:
    """Return the metric bounds of the grid footprint (outer cell edges)."""

    grid = get_grid(manifest)
    min_x = grid["c"]
    max_x = grid["c"] + grid["a"] * grid["cols"]
    max_y = grid["f"]
    min_y = grid["f"] + grid["e"] * grid["rows"]
    return {"minX": min_x, "minY": min_y, "maxX": max_x, "maxY": max_y}


def pixel_to_xy(
    row: int | float,
    col: int | float,
    manifest: Mapping[str, Any],
) -> list[float]:
    """Convert a pixel index to the centre of that cell in local metres.

    ``row=0`` is the North edge and ``col=0`` is the West edge. Raises
    :class:`IndexError` when the pixel is outside the grid and
    :class:`ManifestError` when the manifest is malformed.
    """

    grid = get_grid(manifest)
    r = float(row)
    c = float(col)
    if not (0 <= r < grid["rows"]):
        raise IndexError(f"row {row!r} outside [0, {grid['rows']})")
    if not (0 <= c < grid["cols"]):
        raise IndexError(f"col {col!r} outside [0, {grid['cols']})")

    x = grid["a"] * (c + 0.5) + grid["b"] * (r + 0.5) + grid["c"]
    y = grid["d"] * (c + 0.5) + grid["e"] * (r + 0.5) + grid["f"]
    # Normalise -0.0 to 0.0 for stable comparisons/serialisation.
    return [x + 0.0, y + 0.0]


def cell_center_xy(row: int, col: int, manifest: Mapping[str, Any]) -> list[float]:
    """Alias of :func:`pixel_to_xy` for callers that think in cell centres."""

    return pixel_to_xy(row, col, manifest)


def xy_to_pixel(
    x_m: float,
    y_m: float,
    manifest: Mapping[str, Any],
) -> list[int] | None:
    """Convert local metres to a ``[row, col]`` pixel index.

    Returns ``None`` when the point lies outside the grid footprint. Points
    exactly on the eastern/northern outer edge are outside (half-open grid).
    """

    grid = get_grid(manifest)
    x = _number(x_m, "x_m")
    y = _number(y_m, "y_m")

    # Inverse of the north-up affine (b = d = 0).
    col = (x - grid["c"]) / grid["a"]
    row = (y - grid["f"]) / grid["e"]

    # Guard against tiny negative values caused by floating-point noise.
    if -1e-9 < col < 0:
        col = 0.0
    if -1e-9 < row < 0:
        row = 0.0

    if not (0 <= col < grid["cols"] and 0 <= row < grid["rows"]):
        return None
    return [int(col), int(row)]


def is_xy_in_bounds(x_m: float, y_m: float, manifest: Mapping[str, Any]) -> bool:
    """True when the local metric point falls inside the grid footprint."""

    return xy_to_pixel(x_m, y_m, manifest) is not None


def xy_outside_message(x_m: float, y_m: float) -> str:
    """Stable human-readable message used by API warnings."""

    return f"position [{x_m}, {y_m}] lies outside the regional grid"
