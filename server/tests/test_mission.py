import pytest
import copy

from server.mission import evaluate_plan, evaluate_rehearsal


def region():
    return {"manifest":{"width":10,"height":2,"cellSizeM":10,"originXY":[0,-20]},
            "elevation":[[0]*10 for _ in range(2)],"slope":[[0.0]*10 for _ in range(2)],
            "mask":[[True]*10 for _ in range(2)],"scienceStops":[{"id":"s","positionXY":[95,-5]}]}


def plan(**overrides):
    return {"baseXY":[5,-5],"targetId":"s","maxSlopeDeg":15,"speedMPerMin":30,
            "totalBudgetMin":180,"reserveMin":20,"dwellMin":10,**overrides}


def test_round_trip_time_is_counted_once():
    result=evaluate_plan(region(),plan())["options"]["shortest"]
    assert result["status"] == "ok"
    assert result["totalDistanceM"] == pytest.approx(180)
    assert result["travelMin"] == pytest.approx(6)
    assert result["totalRequiredMin"] == pytest.approx(36)
    assert result["marginMin"] == pytest.approx(144)
    assert result["outbound"] is not result["return"]
    assert result["outbound"]["travelMin"] == pytest.approx(3)
    assert result["return"]["travelMin"] == pytest.approx(3)


def test_over_budget_is_not_no_path_and_bad_constraints_invalid():
    assert evaluate_plan(region(),plan(totalBudgetMin=25))["options"]["shortest"]["status"] == "over_budget"
    with pytest.raises(ValueError):
        evaluate_plan(region(),plan(speedMPerMin=0))
    with pytest.raises(ValueError, match="unknown science stop"):
        evaluate_plan(region(),plan(targetId="missing"))


def test_exact_900m_reference_arithmetic():
    r = region()
    r["manifest"] = {"width":91,"height":1,"cellSizeM":10,"originXY":[0,-10]}
    r["elevation"], r["slope"], r["mask"] = [[0]*91], [[0.0]*91], [[True]*91]
    r["scienceStops"][0]["positionXY"] = [905,-5]
    result = evaluate_plan(r, plan())["options"]["shortest"]
    assert result["outbound"]["distanceM"] == result["return"]["distanceM"] == 900
    assert result["totalRequiredMin"] == 90
    assert result["marginMin"] == 90


def test_rehearsal_respects_remaining_budget_without_subtracting_elapsed():
    request={"baseXY":[5,-5],"currentXY":[45,-5],"targetId":"s","selectedRouteMode":"shortest",
             "maxSlopeDeg":15,"speedMPerMin":10,"remainingBudgetMin":20,"elapsedMin":100,
             "remainingDwellMin":5,"reserveMin":5}
    result=evaluate_rehearsal(region(),request)
    assert result["immediateReturn"]["totalRequiredMin"] == pytest.approx(9)
    assert result["immediateReturn"]["status"] == "ok"
    assert result["continueThenReturn"]["totalRequiredMin"] == pytest.approx(24)
    assert result["continueThenReturn"]["status"] == "over_budget"
    assert result["continueThenReturn"]["currentToTarget"]["status"] == "ok"
    assert "elapsedMin" not in result["continueThenReturn"]


def test_blocked_current_position_is_invalid_and_reported():
    request={"baseXY":[5,-5],"currentXY":[45,-5],"targetId":"s","selectedRouteMode":"shortest",
             "maxSlopeDeg":15,"speedMPerMin":10,"remainingBudgetMin":20,"elapsedMin":0,
             "remainingDwellMin":0,"reserveMin":0,"blockedPolygonsXY":[[[49,-20],[51,-20],[51,0],[49,0]]]}
    result=evaluate_rehearsal(region(),request)
    assert result["immediateReturn"]["status"] == "invalid_input"
    assert result["immediateReturn"]["return"]["pathXY"] is None
    assert "current position is blocked" in result["immediateReturn"]["message"]


def test_event_reset_restores_rehearsal_result():
    request={"baseXY":[5,-5],"currentXY":[45,-5],"targetId":"s","selectedRouteMode":"shortest",
             "maxSlopeDeg":15,"speedMPerMin":10,"remainingBudgetMin":20,"elapsedMin":0,
             "remainingDwellMin":0,"reserveMin":0}
    clear = evaluate_rehearsal(region(), request)
    changed = copy.deepcopy(request)
    changed["blockedPolygonsXY"] = [[[29,-20],[31,-20],[31,0],[29,0]]]
    blocked = evaluate_rehearsal(region(), changed)
    assert blocked["immediateReturn"]["status"] == "no_path"
    assert evaluate_rehearsal(region(), request) == clear
