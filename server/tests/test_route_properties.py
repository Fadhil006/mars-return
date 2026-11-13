"""Small seeded grids checked against an independent, explicit-graph oracle."""

import itertools
import math
import random

import pytest

from server.routing import route


def region(width, height, size=10):
    return {
        "manifest": {"width": width, "height": height, "cellSizeM": size, "originXY": [100, -200]},
        "elevation": [[0.0] * width for _ in range(height)],
        "slope": [[0.0] * width for _ in range(height)],
        "mask": [[True] * width for _ in range(height)],
    }


def xy(r, cell):
    row, col = cell
    m = r["manifest"]
    return [100 + (col + 0.5) * m["cellSizeM"],
            -200 + (m["height"] - row - 0.5) * m["cellSizeM"]]


def graph(r, mode, limit):
    """Build undirected edges from cell pairs, without production routing helpers."""
    cells = {
        (row, col)
        for row in range(r["manifest"]["height"])
        for col in range(r["manifest"]["width"])
        if r["mask"][row][col]
        and all(isinstance(value, (int, float)) and math.isfinite(value)
                for value in (r["elevation"][row][col], r["slope"][row][col]))
        and r["slope"][row][col] <= limit
    }
    edges = {cell: {} for cell in cells}
    for a, b in itertools.combinations(sorted(cells), 2):
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        if max(dr, dc) != 1:
            continue
        if dr and dc and not {(a[0], b[1]), (b[0], a[1])} <= cells:
            continue
        length = r["manifest"]["cellSizeM"] * math.hypot(dr, dc)
        slope = max(r["slope"][a[0]][a[1]], r["slope"][b[0]][b[1]])
        cost = length if mode == "shortest" else length * (1 + 4 * (slope / limit) ** 2)
        edges[a][b] = edges[b][a] = cost
    return edges


def dijkstra(edges, start, goal):
    # Linear minimum selection on tiny graphs keeps this independent of A*'s heap.
    remaining = set(edges)
    costs = dict.fromkeys(edges, math.inf)
    costs[start] = 0.0
    while remaining:
        cell = min(remaining, key=lambda node: (costs[node], node))
        if cell == goal or math.isinf(costs[cell]):
            return costs[goal]
        remaining.remove(cell)
        for neighbor, weight in edges[cell].items():
            if neighbor in remaining:
                costs[neighbor] = min(costs[neighbor], costs[cell] + weight)
    return math.inf


@pytest.mark.parametrize("mode", ["shortest", "slope_penalized"])
def test_seeded_tiny_grids_match_independent_dijkstra(mode):
    rng = random.Random(20261113)
    statuses = set()
    for case in range(48):
        width, height = rng.randint(2, 6), rng.randint(2, 6)
        r = region(width, height, rng.choice([1, 2.5, 10]))
        limit = rng.choice([5, 15, 30])
        for row in range(height):
            for col in range(width):
                r["mask"][row][col] = rng.random() > 0.2
                r["elevation"][row][col] = rng.uniform(-20, 20)
                if rng.random() < 0.12:
                    r["elevation"][row][col] = rng.choice([None, float("nan")])
                r["slope"][row][col] = rng.choice([0, limit / 3, limit, limit + 1, float("inf")])
        start, goal = (0, 0), (height - 1, width - 1)
        for row, col in (start, goal):
            r["mask"][row][col] = True
            r["elevation"][row][col] = 0
            r["slope"][row][col] = 0
        # Include open grids as well as heavily fragmented no-data terrain.
        if case % 6 == 0:
            r["mask"] = [[True] * width for _ in range(height)]
            r["elevation"] = [[0.0] * width for _ in range(height)]
            r["slope"] = [[rng.uniform(0, limit) for _ in range(width)] for _ in range(height)]
        edges = graph(r, mode, limit)
        expected = dijkstra(edges, start, goal)
        result = route(r, xy(r, start), xy(r, goal), mode, limit)
        context = f"seed=20261113 case={case} mode={mode}"
        statuses.add(result["status"])
        assert result["status"] == ("no_path" if math.isinf(expected) else "ok"), context
        if math.isinf(expected):
            assert result["pathXY"] is None, context
            assert result["cost"] is None, context
            continue
        assert result["cost"] == pytest.approx(expected), context
        by_xy = {tuple(xy(r, cell)): cell for cell in edges}
        path = [by_xy[tuple(point)] for point in result["pathXY"]]
        assert (path[0], path[-1]) == (start, goal), context
        assert all(b in edges[a] for a, b in zip(path, path[1:])), context
        assert sum(edges[a][b] for a, b in zip(path, path[1:])) == pytest.approx(expected), context
    assert statuses == {"ok", "no_path"}


@pytest.mark.parametrize("mode", ["shortest", "slope_penalized"])
@pytest.mark.parametrize("obstruction", ["mask", "elevation", "slope", "ceiling"])
def test_diagonal_cannot_cross_unavailable_side_cells(mode, obstruction):
    r = region(2, 2)
    for row, col in ((0, 1), (1, 0)):
        if obstruction == "ceiling":
            r["slope"][row][col] = 16
        else:
            r[obstruction][row][col] = {"mask": False, "elevation": None, "slope": float("nan")}[obstruction]
    result = route(r, xy(r, (0, 0)), xy(r, (1, 1)), mode, 15)
    assert result["status"] == "no_path"
    assert result["pathXY"] is None


def test_mean_slope_weights_edge_maxima_by_distance_not_sample_count():
    r = region(3, 2)
    r["slope"] = [[0, 3, 9], [0, 3, 9]]
    result = route(r, xy(r, (0, 0)), xy(r, (1, 2)), "shortest", 15)
    assert result["status"] == "ok"
    profile = result["profile"]
    lengths = [b["distanceM"] - a["distanceM"] for a, b in zip(profile, profile[1:])]
    assert sorted(lengths) == pytest.approx([10, 10 * math.sqrt(2)])
    slopes = [max(a["slopeDeg"], b["slopeDeg"]) for a, b in zip(profile, profile[1:])]
    expected = sum(length * slope for length, slope in zip(lengths, slopes)) / sum(lengths)
    assert result["distanceM"] == pytest.approx(10 * (1 + math.sqrt(2)))
    assert result["meanSlopeDeg"] == pytest.approx(expected)
    assert result["meanSlopeDeg"] != pytest.approx(sum(slopes) / len(slopes))
