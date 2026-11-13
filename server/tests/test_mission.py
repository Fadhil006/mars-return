"""Mission arithmetic tests: round trips, slopes, budgets, rehearsals."""

from __future__ import annotations

import math

import numpy as np

from server.mission import evaluate_plan, evaluate_rehearsal
from server.tests.helpers import (
    make_region,
    make_stop,
    rehearsal_request_for,
    request_for,
)


def corridor_region(*, slope_value: float = 0.0, elevation_mode: str = "flat"):
    rows, cols, cell = 3, 91, 10.0
    if elevation_mode == "plane":
        xs = (np.arange(cols) + 0.5) * cell
        elevation = np.tile(xs * 0.01, (rows, 1))
        slope = np.full((rows, cols), math.degrees(math.atan(0.01)))
    else:
        elevation = np.zeros((rows, cols))
        slope = np.full((rows, cols), slope_value)
    stop = make_stop("target", (905.0, 5.0))
    return make_region(
        rows=rows,
        cols=cols,
        cell_size_m=cell,
        elevation=elevation,
        slope=slope,
        stops=[stop],
    )


def test_round_trip_time_arithmetic_900m():
    region = corridor_region()
    request = request_for(region, base_xy=(5.0, 5.0), target_id="target", budget=180.0)
    result = evaluate_plan(region, request)

    assert result["status"] == "ok"
    shortest = result["routes"]["shortest"]
    assert shortest["outbound"]["distanceM"] == 900.0
    assert shortest["return"]["distanceM"] == 900.0
    assert shortest["outbound"]["travelMin"] == 30.0
    assert shortest["return"]["travelMin"] == 30.0
    # 900 m out + 900 m back at 30 m/min + 10 min dwell + 20 min reserve = 90 min.
    assert shortest["totalRequiredMin"] == 90.0
    assert shortest["marginMin"] == 90.0
    assert shortest["status"] == "ok"
    assert result["routes"]["slope_penalized"]["totalRequiredMin"] == 90.0


def test_over_budget_sets_margin_and_status():
    region = corridor_region()
    request = request_for(region, budget=50.0)
    result = evaluate_plan(region, request)
    assert result["status"] == "over_budget"
    for route_result in result["routes"].values():
        assert route_result["status"] == "over_budget"
        assert route_result["marginMin"] == -40.0
        assert route_result["pathXY"] is not None


def test_known_plane_ascent_and_slope():
    region = corridor_region(elevation_mode="plane")
    request = request_for(region)
    result = evaluate_plan(region, request)
    route_result = result["routes"]["shortest"]

    assert result["status"] == "ok"
    assert route_result["outbound"]["ascentM"] == 9.0
    expected_slope = round(math.degrees(math.atan(0.01)), 2)
    assert route_result["outbound"]["maxSlopeDeg"] == expected_slope
    assert route_result["outbound"]["meanSlopeDeg"] == expected_slope
    profile = route_result["outbound"]["profile"]
    assert profile[0]["distanceM"] == 0.0
    assert profile[-1]["distanceM"] == 900.0
    assert profile[0]["elevationM"] == 0.05
    assert profile[-1]["elevationM"] == 9.05


def test_profile_is_bounded_and_distance_monotonic():
    region = corridor_region()
    result = evaluate_plan(region, request_for(region))
    for route_result in result["routes"].values():
        for leg_name in ("outbound", "return"):
            profile = route_result[leg_name]["profile"]
            assert 2 <= len(profile) <= 64
            distances = [sample["distanceM"] for sample in profile]
            assert distances == sorted(distances)
        combined = route_result["profile"]
        assert combined[-1]["distanceM"] == route_result["distanceM"]


def test_no_path_nulls_never_zero():
    region = corridor_region()
    mask = region.grid.mask.copy()
    mask[:, 45] = False
    region.grid.mask = mask
    result = evaluate_plan(region, request_for(region))

    assert result["status"] == "no_path"
    for route_result in result["routes"].values():
        assert route_result["status"] == "no_path"
        assert route_result["pathXY"] is None
        assert route_result["distanceM"] is None
        assert route_result["ascentM"] is None
        assert route_result["maxSlopeDeg"] is None
        assert route_result["meanSlopeDeg"] is None
        assert route_result["travelMin"] is None
        assert route_result["totalRequiredMin"] is None
        assert route_result["marginMin"] is None
        assert route_result["profile"] == []
        for leg_name in ("outbound", "return"):
            leg = route_result[leg_name]
            assert leg["pathXY"] is None
            assert leg["distanceM"] is None
            assert leg["profile"] == []


def test_invalid_inputs_are_explicit():
    region = corridor_region()
    cases = [
        ("speed", request_for(region, speed=0.0), "invalid_speed"),
        ("negative budget", request_for(region, budget=-1.0), "invalid_budget"),
        ("reserve over budget", request_for(region, budget=10.0, reserve=20.0), "invalid_budget"),
        ("slope range", request_for(region, max_slope_deg=4.0), "invalid_max_slope"),
        ("unknown target", request_for(region, target_id="nope"), "unknown_target"),
        ("base outside", request_for(region, base_xy=(-10.0, 5.0)), "base_out_of_bounds"),
    ]
    for label, request, code in cases:
        result = evaluate_plan(region, request)
        assert result["status"] == "invalid_input", label
        assert any(error["code"] == code for error in result["errors"]), (label, result["errors"])
        for route_result in result["routes"].values():
            assert route_result["status"] == "invalid_input"
            assert route_result["pathXY"] is None
            assert route_result["distanceM"] is None

    wrong_version = request_for(region)
    wrong_version["datasetVersion"] = "other-dataset"
    result = evaluate_plan(region, wrong_version)
    assert result["status"] == "invalid_input"
    assert any(error["code"] == "unsupported_dataset_version" for error in result["errors"])

    wrong_schema = request_for(region)
    wrong_schema["schemaVersion"] = 2
    result = evaluate_plan(region, wrong_schema)
    assert result["status"] == "invalid_input"
    assert any(error["code"] == "unsupported_schema_version" for error in result["errors"])


def test_rehearsal_return_only_vs_continue():
    region = corridor_region()
    request = rehearsal_request_for(
        region,
        current_xy=(405.0, 5.0),
        base_xy=(5.0, 5.0),
        remaining=60.0,
        elapsed=20.0,
    )
    result = evaluate_rehearsal(region, request)

    assert result["status"] == "over_budget"
    assert result["currentPositionValid"] is True
    immediate = result["immediateReturn"]
    assert immediate["status"] == "ok"
    assert immediate["distanceM"] == 400.0
    assert immediate["totalRequiredMin"] == 33.33  # 400/30 + 20 reserve
    assert immediate["marginMin"] == 26.67

    continuing = result["continueThenReturn"]
    assert continuing["status"] == "over_budget"
    assert continuing["distanceM"] == 1400.0
    assert continuing["totalRequiredMin"] == 76.67  # (500+900)/30 + 10 dwell + 20 reserve
    assert continuing["marginMin"] == -16.67


def test_rehearsal_does_not_subtract_elapsed_twice():
    region = corridor_region()
    base_request = rehearsal_request_for(region, elapsed=0.0, remaining=60.0)
    late_request = rehearsal_request_for(region, elapsed=999.0, remaining=60.0)
    early = evaluate_rehearsal(region, base_request)
    late = evaluate_rehearsal(region, late_request)

    assert early["immediateReturn"]["totalRequiredMin"] == late["immediateReturn"]["totalRequiredMin"]
    assert early["continueThenReturn"]["totalRequiredMin"] == late["continueThenReturn"]["totalRequiredMin"]
    assert late["elapsedMin"] == 999.0
    assert late["remainingBudgetMin"] == 60.0


def test_rehearsal_closure_invalidates_current_without_teleport():
    region = corridor_region()
    closure = [[[395.0, 0.0], [415.0, 0.0], [415.0, 10.0], [395.0, 10.0]]]
    request = rehearsal_request_for(
        region,
        current_xy=(405.0, 5.0),
        blocked=closure,
    )
    result = evaluate_rehearsal(region, request)

    assert result["status"] == "invalid_input"
    assert result["currentPositionValid"] is False
    assert result["currentXY"] == [405.0, 5.0]
    assert any(error["code"] == "current_position_blocked" for error in result["errors"])
    assert result["immediateReturn"]["status"] == "invalid_input"
    assert result["immediateReturn"]["pathXY"] is None


def test_rehearsal_closure_can_make_return_impossible():
    region = corridor_region()
    mask = region.grid.mask.copy()
    mask[:, 20] = False
    region.grid.mask = mask
    request = rehearsal_request_for(region, current_xy=(405.0, 5.0))
    result = evaluate_rehearsal(region, request)

    assert result["status"] == "no_path"
    assert result["currentPositionValid"] is True
    assert result["immediateReturn"]["status"] == "no_path"
    assert result["immediateReturn"]["distanceM"] is None
    assert result["continueThenReturn"]["status"] == "no_path"


def test_rehearsal_invalid_remaining_budget():
    region = corridor_region()
    request = rehearsal_request_for(region, remaining=-1.0)
    result = evaluate_rehearsal(region, request)
    assert result["status"] == "invalid_input"
    assert any(error["code"] == "invalid_remaining" for error in result["errors"])
