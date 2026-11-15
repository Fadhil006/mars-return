"""Line of sight to the hypothetical base, on explicitly synthetic terrain with known answers."""

from fastapi.testclient import TestClient
import pytest

from server.api import create_app
from server.contact import viewshed
from server.mission import evaluate_plan, evaluate_rehearsal
from server.models import PlanResponse


def ridge_region(ridge_m=10.0, mask_hole=None):
    """3 x 20 cells of 10 m, flat at 0 m with a wall of ridge_m across column 5. Slope is left at 0 so routing
    ignores the ridge and only line of sight sees it."""
    elevation = [[ridge_m if col == 5 else 0.0 for col in range(20)] for _ in range(3)]
    mask = [[True] * 20 for _ in range(3)]
    if mask_hole:
        mask[mask_hole[0]][mask_hole[1]] = False
    return {"manifest": {"width": 20, "height": 3, "cellSizeM": 10, "originXY": [0, 0], "datasetVersion": "synthetic-v1"},
            "elevation": elevation, "slope": [[0.0] * 20 for _ in range(3)], "mask": mask,
            "scienceStops": [{"id": "stop", "positionXY": [195, 15], "sourceIds": []}]}


def request(**changes):
    return {"baseXY": [5, 15], "targetId": "stop", "maxSlopeDeg": 15, "speedMPerMin": 10, "totalBudgetMin": 500,
            "reserveMin": 0, "dwellMin": 10, **changes}


def test_flat_terrain_is_fully_visible():
    flat = ridge_region(ridge_m=0.0)
    assert viewshed(flat, [5, 15]).all()
    shortest = evaluate_plan(flat, request())["options"]["shortest"]
    assert shortest["outOfContactMin"] == 0 and shortest["longestOutOfContactMin"] == 0
    assert shortest["contactStatus"] == "within_rule"


def test_ridge_hides_everything_behind_it():
    visible = viewshed(ridge_region(), [5, 15])
    assert visible[1, :6].all() and not visible[1, 6:].any()


def test_blind_walk_and_blind_stop_add_up():
    # 14 blind steps of 10 m each way at 10 m/min, plus 10 min waiting at a stop the base cannot see.
    shortest = evaluate_plan(ridge_region(), request())["options"]["shortest"]
    assert shortest["outbound"]["outOfContactMin"] == pytest.approx(14)
    assert shortest["outbound"]["inContact"] == [True] * 6 + [False] * 14
    assert shortest["outOfContactMin"] == pytest.approx(38)
    assert shortest["longestOutOfContactMin"] == pytest.approx(38)
    assert shortest["contactStatus"] == "exceeds_rule"


def test_rule_threshold_is_inclusive():
    assert evaluate_plan(ridge_region(), request(maxOutOfContactMin=38))["options"]["shortest"]["contactStatus"] == "within_rule"
    assert evaluate_plan(ridge_region(), request(maxOutOfContactMin=37.9))["options"]["shortest"]["contactStatus"] == "exceeds_rule"


def test_contact_rule_never_changes_the_time_verdict():
    shortest = evaluate_plan(ridge_region(), request())["options"]["shortest"]
    assert shortest["status"] == "ok" and shortest["contactStatus"] == "exceeds_rule"


def test_taller_mast_never_sees_less():
    region = ridge_region(ridge_m=3.0)
    low, high = viewshed(region, [5, 15], 1.0), viewshed(region, [5, 15], 20.0)
    assert (high >= low).all() and high.sum() > low.sum()


def test_missing_data_blocks_the_sight_line():
    # Interpolation touches the four surrounding cells, so a ray passing within one cell of a gap is blocked.
    visible = viewshed(ridge_region(ridge_m=0.0, mask_hole=(0, 3)), [5, 15])
    assert not visible[0, 3] and not visible[0, 10]
    assert visible[2, 10] and visible[1, 10]  # rays that never come near the gap still see


def test_rehearsal_from_a_blind_position_reports_contact():
    result = evaluate_rehearsal(ridge_region(), request(selectedRouteMode="shortest", currentXY=[105, 15],
                                                        elapsedMin=20, remainingBudgetMin=200,
                                                        remainingDwellMin=10))
    assert result["immediateReturn"]["outOfContactMin"] == pytest.approx(5)
    assert result["continueThenReturn"]["contactStatus"] == "exceeds_rule"


def test_plan_api_returns_the_contact_grid():
    response = TestClient(create_app(region=ridge_region())).post("/api/plan", json={
        "requestId": "r", "schemaVersion": 1, "datasetVersion": "synthetic-v1", "baseXY": [5, 15], "targetId": "stop",
        "speedMPerMin": 10, "reserveMin": 0, "maxOutOfContactMin": 20})
    assert response.status_code == 200, response.text
    value = PlanResponse.model_validate(response.json())
    assert len(value.contact.visible) == 3 and len(value.contact.visible[0]) == 20
    assert value.contact.maxOutOfContactMin == 20 and value.options.shortest.contactStatus == "exceeds_rule"


def test_assistant_cites_stored_contact_numbers():
    client = TestClient(create_app(region=ridge_region()))
    plan = client.post("/api/plan", json={"requestId": "r", "schemaVersion": 1, "datasetVersion": "synthetic-v1",
                                          "baseXY": [5, 15], "targetId": "stop", "speedMPerMin": 10, "reserveMin": 0}).json()
    value = client.post("/api/brief", json={"requestId": "b", "planId": plan["planId"], "selectedRouteMode": "shortest",
                                            "question": "Can we still get back?"}).json()
    assert "longest continuous stretch is 38.0 min, exceeding the hypothetical 15.0 min contact rule" in value["answer"]
    assert "shortest.contactStatus" in value["metricRefs"]
