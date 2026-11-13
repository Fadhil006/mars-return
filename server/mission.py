"""Round-trip and mid-mission time-budget calculations."""

import math

from server.routing import route


def _valid(value, positive=False):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and (value > 0 if positive else value >= 0)


def _leg(region, start, end, request, mode):
    result = route(region, start, end, mode, request["maxSlopeDeg"], request.get("blockedPolygonsXY", []))
    if result["status"] == "ok":
        result["travelMin"] = result["distanceM"] / request["speedMPerMin"]
        if not math.isfinite(result["travelMin"]):
            raise ValueError("speedMPerMin is too small to produce a finite travel time")
    return result


def _assessment(legs, speed, budget, reserve, dwell):
    distances = [leg.get("distanceM") for leg in legs]
    message = next((leg.get("message") for leg in legs if leg.get("message")), None)
    if any(distance is None for distance in distances):
        status = "no_path" if any(leg.get("status") == "no_path" for leg in legs) else "invalid_input"
        assessment = {"status": status, "totalDistanceM": None, "travelMin": None, "dwellMin": dwell,
                      "reserveMin": reserve, "totalRequiredMin": None, "marginMin": None}
        if message:
            assessment["message"] = message
        return assessment
    total_distance = sum(distances)
    travel = total_distance / speed
    required = travel + dwell + reserve
    if not math.isfinite(required):
        raise ValueError("Scenario produces a non-finite required time")
    return {"status": "ok" if required <= budget else "over_budget", "totalDistanceM": total_distance,
            "travelMin": travel, "dwellMin": dwell, "reserveMin": reserve,
            "totalRequiredMin": required, "marginMin": budget - required}


def _validate_request(request, fields):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    for field in fields:
        if not _valid(request.get(field), positive=field in ("speedMPerMin", "maxSlopeDeg")):
            raise ValueError(f"{field} must be a finite {'positive' if field in ('speedMPerMin', 'maxSlopeDeg') else 'nonnegative'} number")


def _stop(region, request):
    stop = next((item for item in region.get("scienceStops", []) if item.get("id") == request.get("targetId")), None)
    if stop is None:
        raise ValueError("unknown science stop")
    return stop


def evaluate_plan(region, request):
    """Evaluate explicit outbound and return legs for both route objectives."""
    _validate_request(request, ("maxSlopeDeg", "speedMPerMin", "totalBudgetMin", "reserveMin", "dwellMin"))
    if request["reserveMin"] > request["totalBudgetMin"]:
        raise ValueError("reserveMin cannot exceed totalBudgetMin")
    stop = _stop(region, request)
    options = {}
    for mode in ("shortest", "slope_penalized"):
        outbound = _leg(region, request.get("baseXY"), stop.get("positionXY"), request, mode)
        returning = _leg(region, stop.get("positionXY"), request.get("baseXY"), request, mode)
        assessment = _assessment((outbound, returning), request["speedMPerMin"], request["totalBudgetMin"],
                                 request["reserveMin"], request["dwellMin"])
        assessment["outbound"], assessment["return"] = outbound, returning
        options[mode] = assessment
    return {"options": options}


def evaluate_rehearsal(region, request):
    """Compare returning now with continuing to the target before returning."""
    _validate_request(request, ("maxSlopeDeg", "speedMPerMin", "remainingBudgetMin", "elapsedMin", "remainingDwellMin", "reserveMin"))
    if request.get("selectedRouteMode") not in ("shortest", "slope_penalized"):
        raise ValueError("selectedRouteMode must be shortest or slope_penalized")
    stop = _stop(region, request)
    mode = request["selectedRouteMode"]
    current, base, target = request.get("currentXY"), request.get("baseXY"), stop.get("positionXY")
    immediate_leg = _leg(region, current, base, request, mode)
    if immediate_leg.get("message", "").startswith("start position is blocked"):
        immediate_leg["message"] = "current position is blocked, over the slope limit, or has unavailable terrain data"
    immediate = _assessment((immediate_leg,), request["speedMPerMin"], request["remainingBudgetMin"],
                            request["reserveMin"], 0)
    immediate["return"] = immediate_leg

    current_to_target = _leg(region, current, target, request, mode)
    if current_to_target.get("message", "").startswith("start position is blocked"):
        current_to_target["message"] = "current position is blocked, over the slope limit, or has unavailable terrain data"
    target_to_base = _leg(region, target, base, request, mode)
    continuation = _assessment((current_to_target, target_to_base), request["speedMPerMin"],
                               request["remainingBudgetMin"], request["reserveMin"], request["remainingDwellMin"])
    continuation["currentToTarget"] = current_to_target
    continuation["targetToBase"] = target_to_base
    return {"immediateReturn": immediate, "continueThenReturn": continuation}
