"""Reproduce real-data scenarios and independent numeric checks without network access."""

import json
import math
from pathlib import Path
from time import perf_counter

import rasterio

from server.coordinates import xy_to_pixel
import statistics

from server.mission import evaluate_plan, evaluate_reach, evaluate_rehearsal, evaluate_stress
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
    # Cross-mission check: Perseverance's own localization elevations against the orbital CTX grid.
    differences, slopes_at_rover = [], []
    for point in region["roverTraverse"]["waypoints"]:
        r, c = xy_to_pixel(*point["xy"], manifest)
        if region["mask"][r][c]:
            differences.append(point["elevationM"] - region["elevation"][r][c])
            slopes_at_rover.append(region["slope"][r][c])
    rover_check = {"roverLocalizations": len(differences), "solRange": region["roverTraverse"]["solRange"],
                   "meanDifferenceM": round(statistics.mean(differences), 3),
                   "medianDifferenceM": round(statistics.median(differences), 3),
                   "standardDeviationM": round(statistics.pstdev(differences), 3),
                   "maxAbsDifferenceM": round(max(abs(d) for d in differences), 3),
                   "maxGridSlopeAtRoverStopDeg": round(max(slopes_at_rover), 3),
                   "definition": "rover elev_geoid minus prepared CTX elevation at the containing 20 m cell"}
    assert abs(rover_check["meanDifferenceM"]) < 5 and rover_check["standardDeviationM"] < 5, "Rover and CTX elevations disagree"
    assert rover_check["maxGridSlopeAtRoverStopDeg"] <= 15, "A real rover stop lies on terrain the default limit excludes"
    sites = []
    for stop in region["scienceStops"]:
        site_plan = evaluate_plan(region, {**plan_request, "requestId": f"site-{stop['id']}", "targetId": stop["id"]})
        stress = evaluate_stress(region, {**plan_request, "requestId": f"stress-{stop['id']}", "targetId": stop["id"],
                                          "selectedRouteMode": "shortest", "closureRadiusM": 60, "closureCount": 8})
        for option in site_plan["options"].values():
            assert option["status"] == "ok", f"{stop['id']} is not reachable within the default budget"
            check_geometry(option)
        shortest = site_plan["options"]["shortest"]
        sites.append({"id": stop["id"], "name": stop["name"], "roundTripM": shortest["totalDistanceM"],
                      "marginMin": shortest["marginMin"], "stressVerdict": stress["verdict"],
                      "closuresSurvived": f"{stress['survivableCount']}/{len(stress['closures'])}",
                      "worstMarginMin": stress["worstMarginMin"],
                      "largestDetourM": max((c["detourM"] for c in stress["closures"] if c["detourM"] is not None), default=None)})
    reach_request = {**common, "requestId": "real-reach", "selectedRouteMode": "shortest", "remainingBudgetMin": 50}
    reach_open = evaluate_reach(region, reach_request)
    reach_closed = evaluate_reach(region, {**reach_request, "blockedPolygonsXY": rehearsal["blockedPolygonsXY"]})
    assert reach_closed["returnableAreaM2"] <= reach_open["returnableAreaM2"], "A closure cannot enlarge the return envelope"
    target_row, target_col = xy_to_pixel(*next(s["positionXY"] for s in region["scienceStops"] if s["id"] == common["targetId"]), manifest)
    assert math.isclose(reach_open["returnMin"][target_row][target_col] * 30, plan["options"]["shortest"]["return"]["distanceM"], abs_tol=1e-6), \
        "Return field and point-to-point return leg disagree"
    envelope = {name: {k: v for k, v in result.items() if k != "returnMin"} for name, result in (("open", reach_open), ("withClosure", reach_closed))}
    report = {"datasetVersion": manifest["datasetVersion"], "modelVersion": "grid-constant-speed-v1",
              "synthetic": False, "scenarioInputsAreHypothetical": True,
              "independentElevationCheck": {"localXY": base, "sourceElevationM": original,
                                            "preparedElevationM": prepared, "differenceM": prepared-original},
              "roverElevationCrossCheck": rover_check, "sampleSites": sites, "returnEnvelope50Min": envelope,
              "geometryCheck": "Each valid leg distance independently summed from returned XY segments",
              "timing": {"planMs": round(plan_ms, 2), "validationTotalMs": round((perf_counter()-start)*1000, 2)},
              "scenarios": [{"name": "default-plan", "request": plan_request, "result": plan},
                            {"name": "closure-return-only", "request": rehearsal, "result": return_only},
                            {"name": "closure-no-path", "request": disconnected_request, "result": disconnected}],
              "limitations": ["No independent three-landmark image/3D registration review completed",
                              "Base is hypothetical; targets are rover localizations at sampling sites, not drill-hole coordinates",
                              "Rover elevations and the CTX grid are compared, not independently surveyed truth",
                              "Timing is one local run, not a service-level guarantee"]}
    (ROOT / "docs/validation-results.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "scenarios"}, indent=2))


if __name__ == "__main__":
    validate_demo()
