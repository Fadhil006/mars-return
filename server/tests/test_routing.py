import math
import heapq

import pytest

from server.routing import route


def region(width=5, height=5):
    return {"manifest":{"width":width,"height":height,"cellSizeM":10,"originXY":[0,-height*10]},
            "elevation":[[float(c) for c in range(width)] for _ in range(height)],
            "slope":[[0.0]*width for _ in range(height)],"mask":[[True]*width for _ in range(height)]}


def test_flat_diagonal_distance_and_profile():
    r=region()
    result=route(r,[5,-5],[45,-45],"shortest",15)
    assert result["status"] == "ok"
    assert result["distanceM"] == pytest.approx(40*math.sqrt(2))
    assert len(result["profile"]) == 5
    assert result["meanSlopeDeg"] == 0
    assert result["effectiveStartXY"] == [5, -5]
    assert result["requestedGoalXY"] == [45, -45]


def reference_cost(r, start, goal, mode, limit):
    """Independent Dijkstra reference for the two documented edge costs."""
    size = r["manifest"]["cellSizeM"]
    queue, costs = [(0, start)], {start: 0}
    while queue:
        cost, cell = heapq.heappop(queue)
        if cost != costs[cell]:
            continue
        if cell == goal:
            return cost
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nxt = cell[0] + dr, cell[1] + dc
                if (dr == dc == 0 or not (0 <= nxt[0] < len(r["mask"]) and 0 <= nxt[1] < len(r["mask"][0]))
                        or not r["mask"][nxt[0]][nxt[1]] or r["slope"][nxt[0]][nxt[1]] > limit):
                    continue
                if dr and dc and (
                    not r["mask"][cell[0]+dr][cell[1]] or not r["mask"][cell[0]][cell[1]+dc]
                    or r["slope"][cell[0]+dr][cell[1]] > limit or r["slope"][cell[0]][cell[1]+dc] > limit
                ):
                    continue
                length = size * (math.sqrt(2) if dr and dc else 1)
                edge_slope = max(r["slope"][cell[0]][cell[1]], r["slope"][nxt[0]][nxt[1]])
                if mode == "slope_penalized":
                    length *= 1 + 4 * (edge_slope / limit) ** 2
                candidate = cost + length
                if candidate < costs.get(nxt, math.inf):
                    costs[nxt] = candidate
                    heapq.heappush(queue, (candidate, nxt))
    return math.inf


def test_both_objectives_match_dijkstra_and_can_choose_different_paths():
    r = region(3, 3)
    r["slope"][1][1] = 10
    start, goal = (1, 0), (1, 2)
    xy_start, xy_goal = [5, -15], [25, -15]
    shortest = route(r, xy_start, xy_goal, "shortest", 15)
    penalized = route(r, xy_start, xy_goal, "slope_penalized", 15)
    assert shortest["cost"] == pytest.approx(reference_cost(r, start, goal, "shortest", 15))
    assert penalized["cost"] == pytest.approx(reference_cost(r, start, goal, "slope_penalized", 15))
    assert shortest["pathXY"] != penalized["pathXY"]
    assert penalized["meanSlopeDeg"] < shortest["meanSlopeDeg"]


def test_mask_wall_gap_and_no_corner_cutting():
    r=region(3,3)
    for row in range(3): r["mask"][row][1]=False
    assert route(r,[5,-5],[25,-25],"shortest",15)["status"] == "no_path"
    r["mask"][2][1]=True
    result=route(r,[5,-5],[25,-25],"shortest",15)
    assert result["status"] == "ok"
    assert result["pathXY"][-1] == [25,-25]


def test_endpoint_is_not_snapped_and_invalid_numeric_rejected():
    r=region()
    assert route(r,[-1,-5],[45,-45])["status"] == "invalid_input"
    assert route(r,[5,-5],[45,-45],max_slope_deg=float("nan"))["status"] == "invalid_input"


def test_polygon_blocks_touched_cells_and_malformed_rejected():
    r=region(3,3)
    assert route(r,[5,-5],[25,-25],blocked_polygons=[[ [9,-1],[21,-1],[21,-29],[9,-29] ]])["status"] == "invalid_input"
    assert route(r,[5,-5],[25,-25],blocked_polygons=[[[1,1],[float("nan"),2],[3,3]]])["status"] == "invalid_input"
    assert route(r,[5,-5],[25,-25],blocked_polygons=[[[0,0],[1,1],[2,2]]])["status"] == "invalid_input"
    assert route(r,[5,-5],[25,-25],blocked_polygons=[[[0,0],[2,2],[0,2],[2,0]]])["status"] == "invalid_input"


def test_slope_ceiling_and_no_data():
    r=region(3,3)
    r["slope"][1][1]=20
    result=route(r,[5,-5],[25,-25],max_slope_deg=15)
    assert result["status"] == "ok"
    assert [15,-15] not in result["pathXY"]
    r["mask"][0][1]=False
    assert route(r,[5,-5],[25,-25])["status"] == "ok"


def test_blocked_endpoints_are_invalid_but_disconnected_valid_endpoints_are_no_path():
    r = region(3, 3)
    r["mask"][0][0] = False
    assert route(r, [5, -5], [25, -25])["status"] == "invalid_input"
    r = region(3, 3)
    for row in range(3):
        r["mask"][row][1] = False
    assert route(r, [5, -15], [25, -15])["status"] == "no_path"


def test_zero_distance_route():
    result = route(region(), [5, -5], [5, -5])
    assert result["status"] == "ok"
    assert result["distanceM"] == result["cost"] == 0
    assert result["effectiveStartXY"] == result["effectiveGoalXY"] == [5, -5]
