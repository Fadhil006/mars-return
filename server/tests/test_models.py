"""Trust-boundary validation and generated schema consistency."""

import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from server.export_schema import OUTPUT, schema_text
from server.models import PlanRequest, RehearsalRequest


def request(**changes):
    return dict(requestId="test", schemaVersion=1, datasetVersion="test-v1",
                baseXY=[10, 10], targetId="stop", **changes)


@pytest.mark.parametrize("changes", [
    {"speedMPerMin": 0}, {"speedMPerMin": float("nan")},
    {"baseXY": [float("inf"), 0]}, {"maxSlopeDeg": 31},
    {"reserveMin": 181}, {"unknown": True},
    {"blockedPolygonsXY": [[[0, 0], [1, 1], [2, 2]]]},
])
def test_invalid_plan(changes):
    value = request()
    value.update(changes)
    with pytest.raises(ValidationError):
        PlanRequest.model_validate(value)


def test_rehearsal_reserve_may_exceed_remaining_time():
    value = request(selectedRouteMode="shortest", currentXY=[10, 10],
                    elapsedMin=100, remainingBudgetMin=5)
    assert RehearsalRequest.model_validate(value).reserveMin == 20


def test_generated_schema_matches():
    assert OUTPUT.read_text() == schema_text()
    schema = json.loads(schema_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator({"$ref": "#/$defs/PlanRequest", "$defs": schema["$defs"]}).validate(request())
