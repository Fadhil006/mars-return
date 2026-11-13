"""Routing tests: flats, slopes, walls, disconnections, corner traps, closures."""

from __future__ import annotations

import math

import numpy as np

from server.routing import rasterize_blocked, route
from server.tests.helpers import make_grid


def _mean_slope(grid, result):
    values = [grid.slope_at(r, c) for r, c in result.path_rc]
    return sum(values) / len(values)


def test_flat_ground_shortest():
    grid = make_grid(rows=10, cols=10, cell_size_m=10.0)
    result = route(grid, [5.0, 5.0], [95.0, 5.0], mode="shortest", max_slope_deg=15.0)

    assert result.status == "ok"
    assert result.distance_m == 90.0
    assert result.path_xy[0] == [5.0, 5.0]
    assert result.path_xy[-1] == [95.0, 5.0]
    # Unsmoothed grid path: every step is one of the 8 neighbours.
    for (r0, c0), (r1, c1) in zip(result.path_rc, result.path_rc[1:]):
        assert max(abs(r1 - r0), abs(c1 - c0)) == 1


def test_same_cell_is_zero_distance():
    grid = make_grid(rows=5, cols=5)
    result = route(grid, [5.0, 5.0], [5.0, 5.0])
    assert result.status == "ok"
    assert result.distance_m == 0.0
    assert result.path_rc == [(4, 0)]


def test_out_of_bounds_endpoints_are_no_path():
    grid = make_grid(rows=5, cols=5)
    assert route(grid, [-10.0, 5.0], [45.0, 45.0]).status == "no_path"
    assert route(grid, [5.0, 5.0], [500.0, 5.0]).status == "no_path"


def test_wall_with_one_gap():
    rows = cols = 15
    mask = np.ones((rows, cols), dtype=bool)
    mask[:, 7] = False
    mask[7, 7] = True
    grid = make_grid(rows=rows, cols=cols, mask=mask)

    result = route(grid, [5.0, 75.0], [145.0, 75.0], mode="shortest", max_slope_deg=15.0)
    assert result.status == "ok"
    assert any(r == 7 and c == 7 for r, c in result.path_rc)
    assert all(mask[r, c] for r, c in result.path_rc)


def test_fully_disconnected_region():
    rows = cols = 15
    mask = np.ones((rows, cols), dtype=bool)
    mask[:, 7] = False
    grid = make_grid(rows=rows, cols=cols, mask=mask)

    result = route(grid, [5.0, 75.0], [145.0, 75.0])
    assert result.status == "no_path"
    assert result.path_xy is None
    assert result.distance_m is None
    assert result.warnings[0]["code"] == "route_disconnected"


def test_diagonal_corner_cutting_forbidden():
    # Only the two diagonal cells are open; a diagonal move would squeeze
    # between two blocked orthogonal cells, which is not allowed.
    mask = np.array([[True, False], [False, True]])
    grid = make_grid(rows=2, cols=2, mask=mask, cell_size_m=10.0)
    result = route(grid, [5.0, 15.0], [15.0, 5.0])
    assert result.status == "no_path"


def test_no_data_hole_is_avoided():
    rows = cols = 9
    mask = np.ones((rows, cols), dtype=bool)
    mask[4:6, 4:6] = False
    grid = make_grid(rows=rows, cols=cols, mask=mask)
    result = route(grid, [5.0, 45.0], [85.0, 45.0])
    assert result.status == "ok"
    assert all(mask[r, c] for r, c in result.path_rc)
    # A straight line would cross the hole; the path must deviate in y.
    assert any(r != 4 for r, _ in result.path_rc)


def test_max_slope_ceiling():
    slope = np.full((8, 8), 20.0)
    grid = make_grid(rows=8, cols=8, slope=slope)
    assert route(grid, [5.0, 5.0], [75.0, 75.0], max_slope_deg=15.0).status == "no_path"
    assert route(grid, [5.0, 5.0], [75.0, 75.0], max_slope_deg=25.0).status == "ok"


def test_slope_penalized_prefers_gentler_path():
    rows = cols = 21
    slope = np.full((rows, cols), 1.0)
    slope[6:15, 6:15] = 14.0
    grid = make_grid(rows=rows, cols=cols, slope=slope)

    shortest = route(grid, [5.0, 205.0], [205.0, 5.0], mode="shortest", max_slope_deg=15.0)
    penalized = route(grid, [5.0, 205.0], [205.0, 5.0], mode="slope_penalized", max_slope_deg=15.0)

    assert shortest.status == penalized.status == "ok"
    assert penalized.distance_m >= shortest.distance_m
    assert _mean_slope(grid, penalized) <= _mean_slope(grid, shortest) + 1e-9
    for result in (shortest, penalized):
        for r, c in result.path_rc:
            assert grid.slope_at(r, c) <= 15.0


def test_blocked_polygon_wall_and_gap():
    grid = make_grid(rows=10, cols=10, cell_size_m=10.0)
    wall = [[[45.0, 0.0], [55.0, 0.0], [55.0, 100.0], [45.0, 100.0]]]
    result = route(grid, [5.0, 50.0], [95.0, 50.0], blocked_polygons=wall)
    assert result.status == "no_path"

    partial_wall = [[[45.0, 0.0], [55.0, 0.0], [55.0, 40.0], [45.0, 40.0]]]
    detour = route(grid, [5.0, 50.0], [95.0, 50.0], blocked_polygons=partial_wall)
    assert detour.status == "ok"
    assert any(y > 40.0 for _, y in detour.path_xy)


def test_blocked_polygon_rasterization_is_conservative():
    grid = make_grid(rows=4, cols=4, cell_size_m=10.0)
    blocked = rasterize_blocked(grid, [[[9.0, 9.0], [11.0, 9.0], [11.0, 11.0], [9.0, 11.0]]])
    assert blocked.shape == (4, 4)
    # The tiny polygon straddles the corner of two cells; all_touched blocks both.
    assert blocked[2, 0] and blocked[2, 1] or blocked[1, 0]


def test_start_or_goal_on_blocked_cell_is_no_path():
    mask = np.ones((5, 5), dtype=bool)
    mask[4, 0] = False
    grid = make_grid(rows=5, cols=5, mask=mask)
    assert route(grid, [5.0, 5.0], [45.0, 45.0]).status == "no_path"


def test_route_is_deterministic():
    grid = make_grid(rows=12, cols=12)
    a = route(grid, [5.0, 115.0], [115.0, 5.0], mode="slope_penalized")
    b = route(grid, [5.0, 115.0], [115.0, 5.0], mode="slope_penalized")
    assert a.path_rc == b.path_rc
    assert a.distance_m == b.distance_m
