"""Generate clearly synthetic API handoff cases: python -m scripts.generate_fixtures."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from server.api import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "shared/fixtures"


def synthetic_region():
    return {"manifest": {"width": 10, "height": 5, "cellSizeM": 10,
                         "originXY": [0, 0], "datasetVersion": "synthetic-development-v1",
                         "sourceIds": ["synthetic-not-mars"]},
            "elevation": [[0.0]*10 for _ in range(5)],
            "slope": [[0.0]*10 for _ in range(5)], "mask": [[True]*10 for _ in range(5)],
            "scienceStops": [{"id": "synthetic-stop", "positionXY": [95, 25],
                              "sourceIds": ["synthetic-not-mars"]}]}


def generate(output=OUTPUT):
    output.mkdir(parents=True, exist_ok=True)
    request = {"requestId": "fixture", "schemaVersion": 1, "datasetVersion": "synthetic-development-v1",
               "baseXY": [5, 25], "targetId": "synthetic-stop"}
    for name in ("success", "identical-routes", "over-budget", "no-path", "invalid-input", "missing-data", "return-only"):
        region = synthetic_region()
        payload = dict(request)
        endpoint = "/api/plan"
        if name == "success":
            region["slope"][2][4:6] = [14.0, 14.0]
        elif name == "over-budget":
            payload["totalBudgetMin"] = 25
        elif name == "no-path":
            for row in region["mask"]:
                row[5] = False
        elif name == "invalid-input":
            payload["speedMPerMin"] = 0
        elif name == "return-only":
            endpoint = "/api/rehearse"
            payload.update(currentXY=[45, 25], selectedRouteMode="shortest", speedMPerMin=10,
                           elapsedMin=100, remainingBudgetMin=20, remainingDwellMin=5, reserveMin=5)
        app = create_app(region=region) if name != "missing-data" else create_app(region_dir=output / "absent")
        with TestClient(app) as client:
            response = client.post(endpoint, json=payload)
        result = response.json()
        if "planId" in result:
            result["planId"] = f"synthetic-fixture-{name}"
        fixture = {"synthetic": True, "description": "Development-only invented grid, not NASA terrain or a scientific result.",
                   "endpoint": endpoint, "request": payload, "httpStatus": response.status_code, "response": result}
        (output / f"{name}.json").write_text(json.dumps(fixture, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    generate()
