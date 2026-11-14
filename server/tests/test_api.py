"""HTTP-to-calculation integration on explicitly synthetic terrain."""

from copy import deepcopy
import json

from fastapi.testclient import TestClient
import pytest

from server.api import create_app
from server.evidence import trusted_context
from server.models import PlanResponse, RehearsalResponse


def region():
    return {"manifest": {"width": 10, "height": 4, "cellSizeM": 10,
                         "originXY": [0, 0], "datasetVersion": "synthetic-v1"},
            "elevation": [[0.0]*10 for _ in range(4)],
            "slope": [[0.0]*10 for _ in range(4)], "mask": [[True]*10 for _ in range(4)],
            "scienceStops": [{"id": "stop", "positionXY": [95, 15], "sourceIds": ["synthetic"]}]}


def payload(**changes):
    return {"requestId": "request-1", "schemaVersion": 1, "datasetVersion": "synthetic-v1",
            "baseXY": [5, 15], "targetId": "stop", **changes}


def test_plan_and_trusted_lookup():
    app = create_app(region=region())
    response = TestClient(app).post("/api/plan", json=payload())
    assert response.status_code == 200, response.text
    value = response.json()
    PlanResponse.model_validate(value)
    shortest = value["options"]["shortest"]
    assert shortest["totalDistanceM"] == pytest.approx(180)
    assert shortest["totalRequiredMin"] == pytest.approx(36)
    assert shortest["outbound"]["travelMin"] == pytest.approx(3)
    context = trusted_context(app.state.store, value["planId"], "synthetic-v1", "shortest")
    assert context["metrics"]["totalDistanceM"] == 180


def test_rehearsal_remaining_time():
    app = create_app(region=region())
    request = payload(selectedRouteMode="shortest", currentXY=[45, 15], elapsedMin=100,
                      remainingBudgetMin=20, remainingDwellMin=5, reserveMin=5, speedMPerMin=10)
    response = TestClient(app).post("/api/rehearse", json=request)
    assert response.status_code == 200, response.text
    value = response.json()
    RehearsalResponse.model_validate(value)
    assert value["immediateReturn"]["totalRequiredMin"] == 9
    assert value["continueThenReturn"]["status"] == "over_budget"


@pytest.mark.parametrize("changes,code", [
    ({"datasetVersion": "stale"}, 409), ({"targetId": "missing"}, 422),
    ({"baseXY": [-1, 15]}, 422), ({"speedMPerMin": 0}, 422),
    ({"schemaVersion": 2}, 422), ({"extra": "reject"}, 422),
])
def test_errors(changes, code):
    response = TestClient(create_app(region=region())).post("/api/plan", json=payload(**changes))
    assert response.status_code == code, response.text
    assert response.json()["requestId"] == "request-1"


def test_no_path_is_successful_model_result_and_data_not_mutated():
    data = region()
    for row in data["mask"]:
        row[5] = False
    before = deepcopy(data)
    client = TestClient(create_app(region=data))
    result = client.post("/api/plan", json=payload())
    assert result.status_code == 200, result.text
    option = result.json()["options"]["shortest"]
    assert option["status"] == "no_path"
    assert option["totalRequiredMin"] is None
    assert data == before


def test_missing_region_and_asset_whitelist(tmp_path):
    client = TestClient(create_app(region_dir=tmp_path))
    assert client.get("/api/region").status_code == 503
    assert client.post("/api/plan", json=payload()).status_code == 503
    client = TestClient(create_app(region=region()))
    assert client.get("/api/assets/manifest.json").status_code == 404


def test_body_limit_and_nonfinite_json():
    client = TestClient(create_app(region=region()))
    assert client.post("/api/plan", content=b"x"*262145).status_code == 413
    invalid = json.dumps(payload(speedMPerMin=float("nan")))
    response = client.post("/api/plan", content=invalid, headers={"content-type": "application/json"})
    assert response.status_code == 422


def test_asset_symlink_cannot_escape_bundle(tmp_path):
    outside = tmp_path / "private.txt"
    outside.write_text("private")
    directory = tmp_path / "region"
    directory.mkdir()
    (directory / "imagery.webp").symlink_to(outside)
    data = region()
    data["directory"] = directory
    client = TestClient(create_app(region=data))
    assert client.get("/api/assets/imagery.webp").status_code == 503
