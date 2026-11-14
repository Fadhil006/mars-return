"""HTTP trust boundaries not covered by the basic API happy-path tests."""

import json
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from server.api import create_app
from server.evidence import trusted_context
from server.tests.test_api import payload, region


@pytest.fixture
def api(monkeypatch):
    app = create_app(region=region())
    save = Mock(wraps=app.state.store.save)
    monkeypatch.setattr(app.state.store, "save", save)
    return TestClient(app, raise_server_exceptions=False), app.state.store, save


def assert_rejected(response, code, request_id="request-1"):
    body = response.json()
    assert body["requestId"] == request_id
    assert body["schemaVersion"] == 1
    assert body["status"] == "invalid_input"
    assert body["error"]["code"] == code
    assert body["error"]["message"]


@pytest.mark.parametrize("polygon", [
    [],
    [[20, 20], [30, 20]],
    [[20, 20], [30, 20], [20, 20]],
    [[20, 20], [30, 20], [30, 30], [30, 20], [20, 30]],
    # Unequal lobes give this crossing nonzero signed area: routing must reject it.
    [[20, 20], [40, 40], [20, 40], [30, 20]],
    [[20, 20], [30], [20, 30]],
])
def test_malformed_polygon_is_not_saved(api, polygon):
    client, _, save = api
    response = client.post("/api/plan", json=payload(blockedPolygonsXY=[polygon]))
    assert response.status_code == 422, response.text
    assert response.json()["status"] == "invalid_input"
    assert response.json()["requestId"] == "request-1"
    save.assert_not_called()


def test_closed_ring_matches_open_polygon(api):
    client, _, _ = api
    polygon = [[39, 21], [41, 21], [41, 29], [39, 29]]
    opened = client.post("/api/plan", json=payload(blockedPolygonsXY=[polygon]))
    closed = client.post("/api/plan", json=payload(blockedPolygonsXY=[polygon + [polygon[0]]]))
    assert opened.status_code == closed.status_code == 200
    assert opened.json()["options"] == closed.json()["options"]


@pytest.mark.parametrize("change", ["polygon", "slope", "mask", "missing_elevation"])
def test_invalidated_current_position_rejects_rehearsal_without_saving(change):
    data = region()
    request = payload(selectedRouteMode="shortest", currentXY=[45, 15],
                      elapsedMin=5, remainingBudgetMin=100)
    if change == "polygon":
        request["blockedPolygonsXY"] = [[[41, 11], [49, 11], [49, 19], [41, 19]]]
    elif change == "slope":
        data["slope"][2][4] = 20
    elif change == "mask":
        data["mask"][2][4] = False
    else:
        data["elevation"][2][4] = None
    app = create_app(region=data)
    app.state.store.save = Mock(wraps=app.state.store.save)
    response = TestClient(app).post("/api/rehearse", json=request)
    assert response.status_code == 422, response.text
    assert_rejected(response, "invalid_scenario")
    assert "current position is blocked" in response.json()["error"]["message"]
    app.state.store.save.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("baseXY", [float("inf"), 15]),
    ("maxSlopeDeg", float("-inf")),
    ("reserveMin", float("nan")),
    ("totalBudgetMin", float("inf")),
    ("dwellMin", float("nan")),
    ("blockedPolygonsXY", [[[0, 0], [1, 0], [0, float("inf")]]]),
    ("speedMPerMin", True),
    ("speedMPerMin", "30"),
])
def test_nonfinite_or_coerced_plan_numbers_are_rejected(api, field, value):
    client, _, save = api
    response = client.post("/api/plan", content=json.dumps(payload(**{field: value})),
                           headers={"content-type": "application/json"})
    assert response.status_code == 422, response.text
    assert_rejected(response, "validation_error")
    save.assert_not_called()


@pytest.mark.parametrize("endpoint", ["plan", "rehearse"])
def test_finite_speed_that_overflows_travel_time_is_rejected(api, endpoint):
    client, _, save = api
    request = payload(speedMPerMin=5e-324)
    if endpoint == "rehearse":
        request.update(selectedRouteMode="shortest", currentXY=[45, 15],
                       elapsedMin=5, remainingBudgetMin=100)
    response = client.post(f"/api/{endpoint}", json=request)
    assert response.status_code == 422, response.text
    assert_rejected(response, "invalid_scenario")
    save.assert_not_called()


@pytest.mark.parametrize("field", ["currentXY", "elapsedMin", "remainingBudgetMin", "remainingDwellMin"])
def test_nonfinite_rehearsal_fields_are_rejected(api, field):
    client, _, save = api
    request = payload(selectedRouteMode="shortest", currentXY=[45, 15],
                      elapsedMin=5, remainingBudgetMin=100)
    request[field] = [float("nan"), 15] if field == "currentXY" else float("inf")
    response = client.post("/api/rehearse", content=json.dumps(request),
                           headers={"content-type": "application/json"})
    assert response.status_code == 422, response.text
    assert_rejected(response, "validation_error")
    save.assert_not_called()


def test_body_limit_accepts_exact_boundary_and_counts_streamed_bytes(api):
    client, _, save = api
    body = json.dumps(payload()).encode()
    body += b" " * (262144 - len(body))
    response = client.post("/api/plan", content=body,
                           headers={"content-type": "application/json"})
    assert response.status_code == 200, response.text
    save.reset_mock()
    response = client.post("/api/plan", content=iter([body, b" "]),
                           headers={"content-type": "application/json"})
    assert response.status_code == 413, response.text
    assert_rejected(response, "request_too_large", request_id=None)
    save.assert_not_called()


def test_stale_rehearsal_cannot_create_evidence_or_replace_prior_plan(api):
    client, store, save = api
    original = client.post("/api/plan", json=payload()).json()
    before = trusted_context(store, original["planId"], "synthetic-v1", "shortest")
    save.reset_mock()
    response = client.post("/api/rehearse", json=payload(
        datasetVersion="stale", selectedRouteMode="shortest", currentXY=[45, 15],
        elapsedMin=5, remainingBudgetMin=100))
    assert response.status_code == 409, response.text
    assert_rejected(response, "dataset_version_mismatch")
    save.assert_not_called()
    with pytest.raises(KeyError):
        trusted_context(store, original["planId"], "stale", "shortest")
    context = trusted_context(store, original["planId"], "synthetic-v1", "shortest")
    assert context["inputHash"] == original["inputHash"]
    assert context == before


@pytest.mark.parametrize("sources", [
    {},
    [{"sourceId": "synthetic", "url": "https://example.test/source"}],
    [{"sourceId": "synthetic", "title": "Source", "url": 42}],
    [{"sourceId": "other", "title": "Source", "url": "https://example.test/source"}],
])
def test_invalid_source_metadata_makes_bundle_unavailable(tmp_path, sources):
    data = region()
    data["manifest"]["sources"] = sources
    for name in ("manifest", "elevation", "slope", "mask"):
        (tmp_path / f"{name}.json").write_text(json.dumps(data[name]))
    (tmp_path / "science-stops.json").write_text(json.dumps(data["scienceStops"]))
    app = create_app(region_dir=tmp_path)
    app.state.store.save = Mock(wraps=app.state.store.save)
    client = TestClient(app)
    for response in (client.get("/api/region"), client.post("/api/plan", json=payload())):
        assert response.status_code == 503, response.text
        assert response.json()["status"] == "data_unavailable"
        assert response.json()["error"]["code"] == "region_unavailable"
    app.state.store.save.assert_not_called()
