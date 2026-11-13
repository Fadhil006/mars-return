"""8-neighbour A* routing over the regional metric grid.

Two route modes are supported:

``shortest``
    Edge cost is the horizontal step distance only.

``slope_penalized``
    Edge cost is ``stepDistance * (1 + 4 * (edgeSlope / slopeLimit)^2)`` where
    ``edgeSlope`` is the larger of the two cell slopes (conservative).

Both modes enforce the maximum-slope ceiling, exclude ``mask == false`` cells
and conservatively rasterised ``blocked_polygons``, and forbid a diagonal move
when either adjacent orthogonal cell is blocked (no corner cutting).
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine

from server.coordinates import pixel_to_xy, xy_to_pixel

__all__ = [
    "Grid",
    "RouteResult",
    "route",
    "rasterize_blocked",
    "step_distance",
    "grid_from_arrays",
]

_MODES = ("shortest", "slope_penalized")
_NEIGHBOURS = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
)


def _warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


@dataclass
class Grid:
    """Routing grid plus its manifest, sharing the regional coordinate system."""

    manifest: Mapping[str, Any]
    elevation: np.ndarray
    slope: np.ndarray
    mask: np.ndarray
    rows: int = field(init=False)
    cols: int = field(init=False)
    cell_size_m: float = field(init=False)
    transform: Affine = field(init=False)

    def __post_init__(self) -> None:
        self.elevation = np.asarray(self.elevation, dtype=np.float64)
        self.slope = np.asarray(self.slope, dtype=np.float64)
        self.mask = np.asarray(self.mask, dtype=bool)
        if self.elevation.ndim != 2:
            raise ValueError("elevation must be 2-D")
        if not (self.elevation.shape == self.slope.shape == self.mask.shape):
            raise ValueError("elevation, slope and mask must share a shape")

        grid = self.manifest.get("grid", {}) if isinstance(self.manifest, Mapping) else {}
        self.rows = int(grid.get("rows", self.elevation.shape[0]))
        self.cols = int(grid.get("cols", self.elevation.shape[1]))
        if (self.rows, self.cols) != self.elevation.shape:
            raise ValueError(
                f"manifest grid {self.rows}x{self.cols} does not match array "
                f"shape {self.elevation.shape}"
            )
        self.cell_size_m = float(grid.get("cellSizeM", 0.0))
        if self.cell_size_m <= 0:
            raise ValueError("grid.cellSizeM must be positive")
        t = grid.get("transform", {})
        self.transform = Affine(
            float(t.get("a", self.cell_size_m)),
            float(t.get("b", 0.0)),
            float(t.get("c", 0.0)),
            float(t.get("d", 0.0)),
            float(t.get("e", -self.cell_size_m)),
            float(t.get("f", self.rows * self.cell_size_m)),
        )

    # -- coordinates -----------------------------------------------------
    def xy_to_pixel(self, x_m: float, y_m: float) -> list[int] | None:
        return xy_to_pixel(x_m, y_m, self.manifest)

    def pixel_to_xy(self, row: int, col: int) -> list[float]:
        return pixel_to_xy(row, col, self.manifest)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    # -- terrain ---------------------------------------------------------
    def elevation_at(self, row: int, col: int) -> float | None:
        if not self.in_bounds(row, col):
            return None
        value = float(self.elevation[row, col])
        return value if math.isfinite(value) else None

    def slope_at(self, row: int, col: int) -> float | None:
        if not self.in_bounds(row, col):
            return None
        value = float(self.slope[row, col])
        return value if math.isfinite(value) else None

    def traversable(self, row: int, col: int, blocked: np.ndarray | None = None) -> bool:
        if not self.in_bounds(row, col):
            return False
        if not bool(self.mask[row, col]):
            return False
        if not math.isfinite(float(self.elevation[row, col])):
            return False
        if not math.isfinite(float(self.slope[row, col])):
            return False
        if blocked is not None and bool(blocked[row, col]):
            return False
        return True

    def step_distance_m(self, dr: int, dc: int) -> float:
        return self.cell_size_m * (math.sqrt(2.0) if dr and dc else 1.0)


def grid_from_arrays(
    manifest: Mapping[str, Any],
    elevation: np.ndarray,
    slope: np.ndarray,
    mask: np.ndarray,
) -> Grid:
    return Grid(manifest=manifest, elevation=elevation, slope=slope, mask=mask)


@dataclass
class RouteResult:
    mode: str
    status: str
    path_rc: list[tuple[int, int]] | None
    path_xy: list[list[float]] | None
    distance_m: float | None
    explored: int = 0
    reason: str | None = None
    warnings: list[dict[str, str]] = field(default_factory=list)


def _validate_blocked_polygons(
    polygons: Sequence[Sequence[Sequence[float]]] | None,
) -> list[list[list[float]]]:
    if polygons is None:
        return []
    cleaned: list[list[list[float]]] = []
    for index, ring in enumerate(polygons):
        if not isinstance(ring, (list, tuple)) or len(ring) < 3:
            raise ValueError(f"blocked polygon {index} must have at least 3 vertices")
        points: list[list[float]] = []
        for point in ring:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError(f"blocked polygon {index} has a malformed vertex")
            x, y = float(point[0]), float(point[1])
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError(f"blocked polygon {index} has a non-finite vertex")
            points.append([x, y])
        cleaned.append(points)
    return cleaned


def rasterize_blocked(
    grid: Grid,
    polygons: Sequence[Sequence[Sequence[float]]] | None,
) -> np.ndarray:
    """Conservatively rasterise blocked polygons onto the grid.

    ``all_touched=True`` means any cell touched by a polygon (including only at
    an edge or corner) is blocked. Unknown/no-data cells are already excluded
    by the mask, so this array only carries closures.
    """

    cleaned = _validate_blocked_polygons(polygons)
    blocked = np.zeros((grid.rows, grid.cols), dtype=bool)
    if not cleaned:
        return blocked

    shapes = [
        {"type": "Polygon", "coordinates": [ring + [ring[0]]]}
        for ring in cleaned
    ]
    mask = rasterize(
        shapes,
        out_shape=(grid.rows, grid.cols),
        transform=grid.transform,
        fill=0,
        default_value=1,
        all_touched=True,
        dtype="uint8",
    )
    blocked |= mask.astype(bool)
    return blocked


def _edge_slope(grid: Grid, a: tuple[int, int], b: tuple[int, int]) -> float | None:
    sa = grid.slope_at(*a)
    sb = grid.slope_at(*b)
    if sa is None or sb is None:
        return None
    return max(sa, sb)


def _no_path(mode: str, reason: str, message: str, explored: int = 0) -> RouteResult:
    return RouteResult(
        mode=mode,
        status="no_path",
        path_rc=None,
        path_xy=None,
        distance_m=None,
        explored=explored,
        reason=reason,
        warnings=[_warning(reason, message, "error")],
    )


def route(
    grid: Grid,
    start_xy: Sequence[float],
    goal_xy: Sequence[float],
    mode: str = "shortest",
    max_slope_deg: float = 15.0,
    blocked_polygons: Sequence[Sequence[Sequence[float]]] | None = None,
) -> RouteResult:
    """Plan a path between two local metric positions.

    Returns an unsmoothed list of cell centres. When no path exists, ``status``
    is ``no_path`` and path/distance are ``None`` (never zero).
    """

    if mode not in _MODES:
        raise ValueError(f"mode must be one of {_MODES}")
    try:
        slope_limit = float(max_slope_deg)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_slope_deg must be numeric") from exc
    if not math.isfinite(slope_limit) or not (5.0 <= slope_limit <= 30.0):
        raise ValueError("max_slope_deg must be within 5..30 degrees")

    if len(start_xy) != 2 or len(goal_xy) != 2:
        raise ValueError("start_xy and goal_xy must be [x_m, y_m]")
    start = grid.xy_to_pixel(float(start_xy[0]), float(start_xy[1]))
    goal = grid.xy_to_pixel(float(goal_xy[0]), float(goal_xy[1]))
    if start is None:
        return _no_path(mode, "start_out_of_bounds", "Start position is outside the regional grid.")
    if goal is None:
        return _no_path(mode, "goal_out_of_bounds", "Goal position is outside the regional grid.")

    blocked = rasterize_blocked(grid, blocked_polygons)
    start_rc = (start[0], start[1])
    goal_rc = (goal[0], goal[1])

    if not grid.traversable(*start_rc, blocked=blocked):
        return _no_path(
            mode,
            "start_blocked",
            "Start cell is no-data, closed, or steeper than the slope ceiling.",
        )
    if not grid.traversable(*goal_rc, blocked=blocked):
        return _no_path(
            mode,
            "goal_blocked",
            "Goal cell is no-data, closed, or steeper than the slope ceiling.",
        )

    if start_rc == goal_rc:
        xy = [grid.pixel_to_xy(*start_rc)]
        return RouteResult(
            mode=mode,
            status="ok",
            path_rc=[start_rc],
            path_xy=xy,
            distance_m=0.0,
            explored=1,
        )

    g_score = np.full((grid.rows, grid.cols), np.inf, dtype=np.float64)
    parent: dict[tuple[int, int], tuple[int, int]] = {}
    g_score[start_rc] = 0.0

    def heuristic(rc: tuple[int, int]) -> float:
        dr = abs(rc[0] - goal_rc[0])
        dc = abs(rc[1] - goal_rc[1])
        return math.hypot(dr, dc) * grid.cell_size_m

    open_heap: list[tuple[float, float, int, int]] = [(heuristic(start_rc), 0.0, start_rc[0], start_rc[1])]
    closed = np.zeros((grid.rows, grid.cols), dtype=bool)
    explored = 0
    found = False

    while open_heap:
        _, g_here, r, c = heapq.heappop(open_heap)
        node = (r, c)
        if closed[node]:
            continue
        if g_here > g_score[node] + 1e-12:
            continue
        closed[node] = True
        explored += 1

        if node == goal_rc:
            found = True
            break

        for dr, dc in _NEIGHBOURS:
            nr, nc = r + dr, c + dc
            if not grid.in_bounds(nr, nc):
                continue
            if not grid.traversable(nr, nc, blocked=blocked):
                continue

            diagonal = bool(dr and dc)
            if diagonal:
                # No corner cutting: both orthogonal neighbours must be free.
                if not grid.traversable(r + dr, c, blocked=blocked):
                    continue
                if not grid.traversable(r, c + dc, blocked=blocked):
                    continue

            edge_slope = _edge_slope(grid, node, (nr, nc))
            if edge_slope is None or edge_slope > slope_limit + 1e-12:
                continue

            step = grid.step_distance_m(dr, dc)
            if mode == "slope_penalized":
                ratio = edge_slope / slope_limit
                cost = step * (1.0 + 4.0 * ratio * ratio)
            else:
                cost = step

            tentative = g_here + cost
            if tentative + 1e-12 < g_score[nr, nc]:
                g_score[nr, nc] = tentative
                parent[(nr, nc)] = node
                heapq.heappush(
                    open_heap,
                    (tentative + heuristic((nr, nc)), tentative, nr, nc),
                )

    if not found:
        return _no_path(
            mode,
            "route_disconnected",
            "No traversable route exists inside the slope ceiling and closures.",
            explored=explored,
        )

    path_rc: list[tuple[int, int]] = [goal_rc]
    cursor = goal_rc
    while cursor != start_rc:
        cursor = parent[cursor]
        path_rc.append(cursor)
    path_rc.reverse()

    distance = 0.0
    for (r0, c0), (r1, c1) in zip(path_rc, path_rc[1:]):
        distance += grid.step_distance_m(r1 - r0, c1 - c0)

    path_xy = [grid.pixel_to_xy(r, c) for r, c in path_rc]
    return RouteResult(
        mode=mode,
        status="ok",
        path_rc=path_rc,
        path_xy=path_xy,
        distance_m=float(distance),
        explored=explored,
    )


def step_distance(grid: Grid, a: tuple[int, int], b: tuple[int, int]) -> float:
    """Horizontal distance between two adjacent grid cells."""

    return grid.step_distance_m(b[0] - a[0], b[1] - a[1])
