"""Reproduce real-data scenarios and independent numeric checks without network access."""

import json
import math
from pathlib import Path
from time import perf_counter

import rasterio

from server.coordinates import xy_to_pixel
from server.mission import evaluate_plan, evaluate_rehearsal
from server.region import load_region

ROOT = Path(__file__).resolve().parents[1]


def check_geometry(assessment):
    for name in ("outbound", "return", "currentToTarget", "targetToBase"):
        leg = assessment.get(name)
        if leg is None or leg["pathXY"] is None:
            continue
        path = leg["pathXY"]
        measured = sum(math.dist(a, b) for a, b in zip(path, path[1:]))
        assert math.isclose(measured, leg["distanceM"], abs_tol=1e-6), "Geometry and distance disagree"


def validate_demo():
    start = perf_counter()
    region = load_region(ROOT / "data/region")
    manifest = region["manifest"]
    base = manifest["scenario"]["baseXY"]
    common = {"schemaVersion": 1, "datasetVersion": manifest["datasetVersion"],
              "baseXY": base, "targetId": manifest["scenario"]["defaultTargetId"],
              "maxSlopeDeg": 15, "speedMPerMin": 30, "reserveMin": 20,
              "blockedPolygonsXY": []}
    plan_request = {**common, "requestId": "real-default", "totalBudgetMin": 180, "dwellMin": 10}
    began = perf_counter()
    plan = evaluate_plan(region, plan_request)
    plan_ms = (perf_counter()-began)*1000
    for result in plan["options"].values():
        assert result["status"] == "ok", "Default real-data scenario is not feasible"
        check_geometry(result)
    shortest_path = plan["options"]["shortest"]["outbound"]["pathXY"]
    current = shortest_path[len(shortest_path)//2]
    rehearsal = {**common, "requestId": "real-return-only", "selectedRouteMode": "shortest",
                 "currentXY": current, "elapsedMin": 130, "remainingBudgetMin": 50, "remainingDwellMin": 10,
                 "blockedPolygonsXY": [[[1200, 1300], [1400, 1300], [1400, 1700], [1200, 1700]]]}
    baseline = evaluate_rehearsal(region, {**rehearsal, "blockedPolygonsXY": []})
    return_only = evaluate_rehearsal(region, rehearsal)
    assert return_only["immediateReturn"]["status"] == "ok"
    assert return_only["continueThenReturn"]["status"] == "over_budget"
    disconnected_request = {**rehearsal, "requestId": "real-disconnected",
                            "blockedPolygonsXY": [[[700, 0], [800, 0], [800, 3000], [700, 3000]]]}
    disconnected = evaluate_rehearsal(region, disconnected_request)
    assert disconnected["immediateReturn"]["status"] == "no_path"
    assert disconnected["continueThenReturn"]["status"] == "no_path"
    for results in (return_only, disconnected):
        for assessment in results.values():
            check_geometry(assessment)
    reset = evaluate_rehearsal(region, {**rehearsal, "blockedPolygonsXY": []})
    assert reset == baseline
    row, col = xy_to_pixel(*base, manifest)
    offset = manifest["sourceBoundsXY"][:2]
    with rasterio.open(ROOT / "data/raw/M20_JezeroCrater_CTXDEM_20m.tif") as source:
        original = float(next(source.sample([(base[0]+offset[0], base[1]+offset[1])]))[0])
    prepared = region["elevation"][row][col]
    assert math.isclose(original, prepared, abs_tol=0.001), "Source and prepared sample differ"
    report = {"datasetVersion": manifest["datasetVersion"], "modelVersion": "grid-constant-speed-v1",
              "synthetic": False, "scenarioInputsAreHypothetical": True,
              "independentElevationCheck": {"localXY": base, "sourceElevationM": original,
                                            "preparedElevationM": prepared, "differenceM": prepared-original},
              "geometryCheck": "Each valid leg distance independently summed from returned XY segments",
              "timing": {"planMs": round(plan_ms, 2), "validationTotalMs": round((perf_counter()-start)*1000, 2)},
              "scenarios": [{"name": "default-plan", "request": plan_request, "result": plan},
                            {"name": "closure-return-only", "request": rehearsal, "result": return_only},
                            {"name": "closure-no-path", "request": disconnected_request, "result": disconnected}],
              "limitations": ["No independent three-landmark image/3D registration review completed",
                              "Targets and base are hypothetical, not registered sample locations",
                              "Timing is one local run, not a service-level guarantee"]}
    (ROOT / "docs/validation-results.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "scenarios"}, indent=2))


if __name__ == "__main__":
    validate_demo()
