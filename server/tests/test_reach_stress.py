"""Return-envelope and closure stress checks on explicitly synthetic terrain."""

import math
import random

from fastapi.testclient import TestClient
import pytest

from scripts.build_science import CROP, RADIUS_M, STANDARD_PARALLEL_DEG, build_science
from server.api import create_app
from server.evidence import trusted_context
from server.mission import evaluate_reach, evaluate_stress
from server.models import ReachResponse, StressResponse
from server.routing import return_field, route


def region(width=12, height=9, walls=()):
    mask = [[True] * width for _ in range(height)]
    for row, col in walls:
        mask[row][col] = False
    return {"manifest": {"width": width, "height": height, "cellSizeM": 10, "originXY": [0, 0],
                         "datasetVersion": "synthetic-v1"},
            "elevation": [[0.0] * width for _ in range(height)], "slope": [[0.0] * width for _ in range(height)],
            "mask": mask, "scienceStops": [{"id": "stop", "positionXY": [115, 45], "sourceIds": ["synthetic"]}]}


def request(**changes):
    return {"requestId": "r", "schemaVersion": 1, "datasetVersion": "synthetic-v1", "baseXY": [5, 45],
            "targetId": "stop", "maxSlopeDeg": 15, "speedMPerMin": 10, "totalBudgetMin": 60, "reserveMin": 5,
            "dwellMin": 5, "blockedPolygonsXY": [], "selectedRouteMode": "shortest", "closureRadiusM": 20,
            "closureCount": 4, **changes}


def test_return_field_agrees_with_point_to_point_routes_on_random_terrain():
    rng = random.Random(7)
    r = region()
    r["slope"] = [[rng.uniform(0, 20) for _ in range(12)] for _ in range(9)]
    r["slope"][4][0] = 0.0
    field = return_field(r, [5, 45], "shortest", 15)
    for row in range(9):
        for col in range(12):
            leg = route(r, [col * 10 + 5, (8 - row) * 10 + 5], [5, 45], "shortest", 15)
            if leg["status"] == "ok":
                assert field[row][col] == pytest.approx(leg["distanceM"])
            else:
                assert field[row][col] is None


def test_return_field_marks_walled_off_cells_unreachable_and_rejects_blocked_base():
    r = region(walls=[(row, 6) for row in range(9)])
    field = return_field(r, [5, 45])
    assert field[4][5] == pytest.approx(50) and field[4][7] is None
    with pytest.raises(ValueError):
        return_field(r, [65, 45])


def test_reach_counts_only_cells_that_fit_budget_after_reserve():
    result = evaluate_reach(region(), {**request(), "remainingBudgetMin": 8})  # 3 walking minutes = 30 m
    assert result["allowanceMin"] == 3 and result["status"] == "ok"
    assert result["reachableAreaM2"] == 12 * 9 * 100
    assert result["returnableAreaM2"] == 18 * 100  # 7 + 5 + 5 + 1 cells within 30 m by 8-neighbour steps
    assert result["farthestReturnableMin"] == pytest.approx(3)
    assert evaluate_reach(region(), {**request(), "remainingBudgetMin": 2, "reserveMin": 5})["status"] == "over_budget"


def test_open_ground_survives_every_single_closure_with_a_detour():
    result = evaluate_stress(region(), request())
    assert result["verdict"] == "robust" and result["survivableCount"] == len(result["closures"]) == 4
    assert all(c["detourM"] > 0 and c["status"] == "ok" for c in result["closures"])
    assert result["worstMarginMin"] == pytest.approx(min(c["marginMin"] for c in result["closures"]))
    home = result["baseline"]["return"]["pathXY"]
    assert all(list(c["centerXY"]) in [list(p) for p in home] for c in result["closures"])


def test_single_gap_in_a_wall_makes_the_return_fragile():
    walls = [(row, 6) for row in range(9) if row != 4]
    result = evaluate_stress(region(walls=walls), request(closureCount=12))
    assert result["verdict"] == "fragile"
    stranded = [c for c in result["closures"] if c["status"] == "no_path"]
    assert stranded and all(c["returnDistanceM"] is None and c["marginMin"] is None for c in stranded)
    assert result["worstMarginMin"] is None


def test_over_budget_detour_is_fragile_and_missing_baseline_is_unavailable():
    assert evaluate_stress(region(), request(totalBudgetMin=33))["verdict"] == "fragile"  # baseline needs 32
    walled = evaluate_stress(region(walls=[(row, 6) for row in range(9)]), request())
    assert walled["verdict"] == "unavailable" and walled["closures"] == []


def test_reach_and_stress_endpoints_return_trusted_records():
    app = create_app(region=region())
    client = TestClient(app)
    base = {k: v for k, v in request().items() if k not in ("targetId", "totalBudgetMin", "dwellMin", "closureRadiusM", "closureCount")}
    reach = client.post("/api/reach", json={**base, "remainingBudgetMin": 30})
    assert reach.status_code == 200, reach.text
    ReachResponse.model_validate(reach.json())
    assert len(reach.json()["returnMin"]) == 9
    stress = client.post("/api/stress", json=request())
    assert stress.status_code == 200, stress.text
    StressResponse.model_validate(stress.json())
    context = trusted_context(app.state.store, stress.json()["planId"], "synthetic-v1", "shortest")
    assert context["metrics"]["verdict"] == "robust"
    assert client.post("/api/reach", json={**base, "remainingBudgetMin": 30, "baseXY": [5000, 5]}).status_code == 422
    assert client.post("/api/stress", json=request(closureCount=13)).status_code == 422


def waypoint(sol, x, y):
    easting, northing = CROP[0] + x, CROP[1] + y
    lon = math.degrees(easting / (RADIUS_M * math.cos(math.radians(STANDARD_PARALLEL_DEG))))
    return {"type": "Feature", "properties": {"sol": sol, "RMC": f"{sol}_0", "easting": easting, "northing": northing,
            "lon": lon, "lat": math.degrees(northing / RADIUS_M), "elev_geoid": -2500.0, "dist_total_m": float(sol)}}


def test_sample_site_uses_last_rover_localization_before_sealing_and_checks_projection():
    points = [waypoint(10, 100, 100), waypoint(20, 200, 300), waypoint(40, 900, 900), waypoint(50, 5000, 100)]
    line = {"type": "Feature", "properties": {"sol": 20}, "geometry": {"type": "LineString",
            "coordinates": [[p["properties"]["lon"], p["properties"]["lat"], 0] for p in points[:2]]}}
    sites = [{"id": "site", "feature": "F", "samplingLocation": "L",
              "samples": [{"number": 1, "name": "S", "type": "Rock Core", "sealedDate": "2021-01-01", "sol": 30, "rockType": "Igneous"}]}]
    stops, layer = build_science({"features": points}, {"features": [line]}, sites)
    assert stops[0]["positionXY"] == [200.0, 300.0] and stops[0]["roverSol"] == 20
    assert [w["sol"] for w in layer["waypoints"]] == [10, 20, 40] and layer["solRange"] == [10, 40]
    assert layer["pathXY"] == [[100.0, 100.0], [200.0, 300.0]]
    points[0]["properties"]["easting"] += 50
    with pytest.raises(ValueError, match="Projection"):
        build_science({"features": points}, {"features": [line]}, sites)
    with pytest.raises(ValueError, match="No in-crop"):
        build_science({"features": [waypoint(50, 5000, 100)] + points[1:3]}, {"features": []},
                      [{**sites[0], "samples": [{**sites[0]["samples"][0], "sol": 60}]}])
