"""Deterministic, evidence-backed briefs built from stored plan metrics.

The brief endpoint never trusts numbers that appear in the user's question. It
reads the server-stored plan record (already evaluated against the dataset) and
the regional science-stop records, then produces a template explanation with
explicit source and metric citations.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from server.mission import Region

__all__ = ["build_brief", "metric_refs_for_route", "source_records_for_brief"]


def _unique(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _fmt(value: Any, unit: str = "") -> str:
    if value is None:
        return "unavailable"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number - round(number)) < 1e-9:
        text = f"{int(round(number)):,}"
    else:
        text = f"{number:,.2f}"
    return f"{text}{unit}"


def metric_refs_for_route(route: Mapping[str, Any], mode: str) -> list[dict[str, Any]]:
    """Concrete metric citations for one route assessment."""

    refs: list[dict[str, Any]] = []
    combined = (
        ("distanceM", "m"),
        ("ascentM", "m"),
        ("maxSlopeDeg", "deg"),
        ("meanSlopeDeg", "deg"),
        ("travelMin", "min"),
        ("totalRequiredMin", "min"),
        ("marginMin", "min"),
    )
    for metric, unit in combined:
        refs.append(
            {
                "metric": metric,
                "value": route.get(metric),
                "unit": unit,
                "routeMode": mode,
                "leg": "combined",
            }
        )
    for leg_name in ("outbound", "return"):
        leg = route.get(leg_name, {})
        refs.append(
            {
                "metric": "distanceM",
                "value": leg.get("distanceM"),
                "unit": "m",
                "routeMode": mode,
                "leg": leg_name,
            }
        )
        refs.append(
            {
                "metric": "travelMin",
                "value": leg.get("travelMin"),
                "unit": "min",
                "routeMode": mode,
                "leg": leg_name,
            }
        )
    return refs


def source_records_for_brief(
    region: Region,
    route: Mapping[str, Any],
    stop: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    ids: list[str] = [str(v) for v in route.get("sourceIds", []) if isinstance(v, str)]
    if stop:
        ids += [str(v) for v in stop.get("sourceIds", []) if isinstance(v, str)]
        if stop.get("sourceId"):
            ids.append(str(stop["sourceId"]))
    records = [region.sources[source_id] for source_id in _unique(ids) if source_id in region.sources]
    return records


def build_brief(
    region: Region,
    plan: Mapping[str, Any],
    plan_request: Mapping[str, Any],
    selected_route_mode: str,
) -> dict[str, Any]:
    """Build a deterministic template brief for a stored plan."""

    routes = plan.get("routes")
    if not isinstance(routes, Mapping) or selected_route_mode not in routes:
        raise ValueError(f"selectedRouteMode {selected_route_mode!r} is not present in the stored plan")
    route = routes[selected_route_mode]
    target_id = str(plan_request.get("targetId", ""))
    stop = region.stop(target_id)
    stop_name = str(stop.get("name")) if stop else target_id

    outbound = route.get("outbound", {})
    return_leg = route.get("return", {})
    status = route.get("status")
    if status == "ok":
        headline = (
            f"The {selected_route_mode} plan reaches {stop_name} and returns to base "
            f"within the { _fmt(plan_request.get('totalBudgetMin'), ' min') } budget."
        )
    elif status == "over_budget":
        headline = (
            f"The {selected_route_mode} plan reaches {stop_name} and returns to base, "
            f"but exceeds the budget by {_fmt(abs(float(route.get('marginMin') or 0.0)), ' min')}."
        )
    elif status == "no_path":
        headline = (
            f"The {selected_route_mode} plan has no traversable route to {stop_name} "
            f"and back under the current slope ceiling and closures."
        )
    else:
        headline = f"The {selected_route_mode} plan for {stop_name} has status {status}."

    body = (
        f" Outbound: {_fmt(outbound.get('distanceM'), ' m')} in "
        f"{_fmt(outbound.get('travelMin'), ' min')}. Return: "
        f"{_fmt(return_leg.get('distanceM'), ' m')} in "
        f"{_fmt(return_leg.get('travelMin'), ' min')}. "
        f"Combined distance {_fmt(route.get('distanceM'), ' m')}, ascent "
        f"{_fmt(route.get('ascentM'), ' m')}, maximum sampled slope "
        f"{_fmt(route.get('maxSlopeDeg'), ' deg')}, distance-weighted mean slope "
        f"{_fmt(route.get('meanSlopeDeg'), ' deg')}. "
        f"Travel {_fmt(route.get('travelMin'), ' min')} + dwell "
        f"{_fmt(route.get('dwellMin'), ' min')} + reserve "
        f"{_fmt(route.get('reserveMin'), ' min')} = "
        f"{_fmt(route.get('totalRequiredMin'), ' min')} required; margin "
        f"{_fmt(route.get('marginMin'), ' min')} against "
        f"{_fmt(plan_request.get('totalBudgetMin'), ' min')}."
    )

    evidence = ""
    if stop:
        provenance = stop.get("provenance", {}) if isinstance(stop.get("provenance"), Mapping) else {}
        evidence = (
            f" Science target {stop_name}: {stop.get('description', '')} "
            f"{stop.get('geology', '')} Provenance: {provenance.get('mission', '')}, "
            f"{provenance.get('site', '')}, sol {provenance.get('sol', 'unknown')}; "
            f"{provenance.get('citation', '')}"
        ).strip()
        evidence = " " + evidence

    records = source_records_for_brief(region, route, stop)
    citations = "; ".join(
        f"[{record['sourceId']}] {record.get('title', '')}"
        + (f" ({record['url']})" if record.get("url") else "")
        for record in records
    )
    citation_text = f" Sources: {citations}." if citations else ""

    answer = (
        headline
        + body
        + evidence
        + citation_text
        + " This explanation is generated from the stored plan record, not from numbers in the question."
    )

    source_ids = _unique([str(record["sourceId"]) for record in records])
    return {
        "requestId": "",
        "planId": str(plan.get("planId", "")),
        "answerText": answer,
        "sourceIds": source_ids,
        "metricRefs": metric_refs_for_route(route, selected_route_mode),
        "mode": "template",
        "datasetVersion": str(plan.get("datasetVersion", region.dataset_version)),
        "modelVersion": str(plan.get("modelVersion", region.model_version)),
        "warnings": list(plan.get("warnings", [])),
    }
