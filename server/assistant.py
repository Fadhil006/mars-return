"""B3 assistant: explains saved calculations. It never calculates, and never trusts numbers in a question."""

import json
import os
import re

from server.evidence import trusted_context

LABELS = {"shortest": "Shortest distance", "slope_penalized": "Lower slope",
          "immediateReturn": "Return now", "continueThenReturn": "Continue to the stop, then return"}
FIELDS = ("status", "totalDistanceM", "travelMin", "dwellMin", "reserveMin", "totalRequiredMin", "marginMin",
          "outOfContactMin", "longestOutOfContactMin", "maxOutOfContactMin", "contactStatus")
LEGS = ("outbound", "return", "currentToTarget", "targetToBase")
LEG_FIELDS = ("distanceM", "ascentM", "maxSlopeDeg", "meanSlopeDeg", "travelMin")
# Checked in order; the first match wins, so unsupported topics are never answered from route data.
TOPICS = (
    ("unsupported", r"weather|storm|dust|wind|temperature|medical|health|oxygen|suit|surviv\w*|die|injur\w*|rock fall|life|water|alien\w*"),
    ("radiation", r"radiation|dose|cosmic"),
    ("limits", r"safe|safety|hazard\w*|obstacle\w*|danger\w*|risk\w*"),
    ("evidence", r"evidence|sources?|samples?|destination|stop|science|scientific|resolution|data|dataset|imagery|elevation|provenance|cit\w+"),
    ("return", r"return\w*|back|home|still|margin|budget|time|late|blocked|closure|corridor|reserve"),
    ("route", r"route\w*|path|why|slope|distance|short\w*|compar\w*|differ\w*|steep\w*|far|long"),
)
CAVEAT = (" The base, speed, slope ceiling, time budget and any closure are hypothetical scenario inputs;"
          " this is a model result, not certified guidance.")
SYSTEM = ("You explain a Mars excursion plan that was already calculated. Use only the supplied facts. Do not calculate,"
          " estimate or add numbers, places, weather, safety or survival claims. Say the base and scenario are"
          " hypothetical. Answer in at most 120 words. Reply with JSON only:"
          ' {"answer": string, "sourceIds": [ids from allowedSourceIds], "metricRefs": [refs from allowedMetricRefs]}')
NUMBER = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?(?!\w)")


def classify(question):
    return next((topic for topic, words in TOPICS if re.search(rf"\b(?:{words})\b", question.lower())), "unsupported")


def _n(value, unit, digits=1):
    return "not available" if value is None else f"{abs(value):.{digits}f} {unit}"


def _assessment_text(name, item, budget, budget_label):
    label = LABELS[name]
    if item["status"] == "no_path":
        return f"{label}: no route was found under the slope ceiling and closures, so no distance or time is available."
    verdict = (f"within the {budget_label} with a margin of {_n(item['marginMin'], 'min')}" if item["status"] == "ok"
               else f"over the {budget_label} by {_n(item['marginMin'], 'min')}")
    return (f"{label}: {_n(item['totalDistanceM'], 'm', 0)} in total; {_n(item['travelMin'], 'min')} travel"
            f" + {_n(item['dwellMin'], 'min')} dwell + {_n(item['reserveMin'], 'min')} reserve"
            f" = {_n(item['totalRequiredMin'], 'min')} required against {_n(budget, 'min')}, {verdict}."
            + _contact_text(item))


def _contact_text(item):
    if item.get("contactStatus") is None:
        return ""
    rule = "exceeding" if item["contactStatus"] == "exceeds_rule" else "within"
    return (f" Out of sight of the base for {_n(item['outOfContactMin'], 'min')} in total; the longest continuous stretch"
            f" is {_n(item['longestOutOfContactMin'], 'min')}, {rule} the hypothetical"
            f" {_n(item['maxOutOfContactMin'], 'min')} contact rule.")


def _slope_text(item):
    parts = [f"{leg} leg maximum slope {_n(item[leg]['maxSlopeDeg'], 'degrees')}, mean {_n(item[leg]['meanSlopeDeg'], 'degrees')},"
             f" ascent {_n(item[leg]['ascentM'], 'm')}" for leg in LEGS
             if item.get(leg) and item[leg].get("maxSlopeDeg") is not None]
    return f" Along the returned path: {'; '.join(parts)}." if parts else ""


def _numbers(value):
    """Every number the model may repeat: numeric facts plus numbers inside fact text (names, dates, resolutions)."""
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return [abs(float(value))]
    if isinstance(value, str):
        return [float(token) for token in NUMBER.findall(value)]
    return [number for item in (value.values() if isinstance(value, dict) else value) for number in _numbers(item)]


def _consistent(answer, allowed):
    for token in NUMBER.findall(answer):
        digits = len(token.partition(".")[2])
        if not any(round(value, digits) == float(token) for value in allowed):
            return False
    return True


def _paths(value, path=()):
    """(path, number) for every number in the facts, including numbers inside text, in document order."""
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        yield path, abs(float(value))
    elif isinstance(value, str):
        for token in NUMBER.findall(value):
            yield path, float(token)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _paths(item, path + (key,))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _paths(item, path)


def _ref(path):
    if path[0] == "assessments":
        return ".".join(path[1:])  # the same <assessment>.<field> form as metricRefs, plus leg fields
    return f"input.{path[1]}" if path[0] == "inputs" else path[0]


UNIT = {"min": "Min", "m": "M", "degrees": "Deg", "°": "Deg"}


def _trace(answer, facts):
    """Each number in an answer with the stored value it repeats: same unit first (min, m, degrees), then planner
    metrics before inputs before records, then fields not already used, so a click lands on the right metric."""
    order = {"assessments": 0, "inputs": 1}
    candidates = list(_paths({k: v for k, v in facts.items() if k != "referenceAnswer"}))
    traced, used = [], set()
    for found in re.finditer(r"(?<![\w.-])(\d+(?:\.\d+)?)(?!\w)\s*(min|m|degrees|°)?", answer):
        token, suffix = found.group(1), UNIT.get(found.group(2) or "")
        digits = len(token.partition(".")[2])
        matches = [path for path, value in candidates if round(value, digits) == float(token)]
        matches.sort(key=lambda path: (suffix is not None and not str(path[-1]).endswith(suffix),
                                       order.get(path[0], 2), _ref(path) in used))
        ref = _ref(matches[0]) if matches else None
        used.add(ref)
        traced.append({"value": token, "ref": ref})
    return traced


def anthropic_complete(prompt):
    import anthropic  # optional dependency: Group A runs without it and without a credential
    client = anthropic.Anthropic(api_key=os.environ["MODEL_API_KEY"], timeout=8.0, max_retries=0)
    response = client.messages.create(model=os.environ.get("MODEL_NAME") or "claude-opus-5-5", max_tokens=2048,
                                      output_config={"effort": "low"}, system=SYSTEM,
                                      messages=[{"role": "user", "content": prompt}])
    if response.stop_reason != "end_turn":  # refusal or truncation: the template answers instead
        raise ValueError(response.stop_reason)
    return "".join(block.text for block in response.content if block.type == "text")


def build_brief(region, store, plan_id, selected_route_mode, question, complete=None):
    """KeyError: plan missing or expired. ValueError: route mode does not match the saved assessment."""
    dataset = region["manifest"]["datasetVersion"]
    context = trusted_context(store, plan_id, dataset, selected_route_mode)
    inputs = store.get(plan_id, dataset)["inputs"]
    metrics = context["metrics"]
    rehearsal = "immediateReturn" in metrics
    items = ({name: metrics[name] for name in ("immediateReturn", "continueThenReturn")} if rehearsal
             else {selected_route_mode: metrics})
    budget = inputs.get("remainingBudgetMin") if rehearsal else inputs.get("totalBudgetMin")
    budget_label = "remaining time" if rehearsal else "time budget"
    stop = next((s for s in region["scienceStops"] if s["id"] == inputs.get("targetId")), None) or {}
    stop_name = stop.get("name") or inputs.get("targetId") or "the selected stop"
    known = {s["sourceId"]: s for s in region.get("sources", [])}
    allowed_sources = sorted(set(known) | set(context["sourceIds"]) | set(stop.get("sourceIds", [])))
    allowed_refs = [f"{name}.{field}" for name in items for field in FIELDS]
    topic = classify(question)

    if topic == "unsupported":
        answer = ("The supplied evidence does not cover this. It covers the calculated route to the selected stop,"
                  " its distance, slope and time margin, and the cited terrain and sampling-site sources.")
        source_ids, refs = [], []
    elif topic == "evidence":
        samples = "; ".join(f"{s.get('name')} ({s.get('type')}, sealed {s.get('sealedDate')})" for s in stop.get("samples", []))
        records = [known[i] for i in stop.get("sourceIds", []) if i in known]
        cited = " ".join(f"[{r['sourceId']}] {r['title']}"
                         + (f", {r['resolution']}" if r.get("resolution") else "")
                         + (f". Limitation: {r['limitations']}" if r.get("limitations") else ".") for r in records)
        answer = " ".join(filter(None, [
            f"{stop_name}: {stop.get('description') or 'no description is recorded for this stop.'}",
            f"Samples recorded there: {samples}." if samples else "",
            f"Location: {stop['locationProvenance']}" if stop.get("locationProvenance") else "",
            f"Sources: {cited}" if cited else "No source record is attached to this stop.",
            "The stop is a recorded position; the base it is reached from is hypothetical."]))
        source_ids, refs = list(stop.get("sourceIds", [])), []
    elif topic == "radiation":
        # The dose shown in the interface is a display estimate made in the browser; the planner never computes it.
        answer = ("The radiation figure shown is a display estimate, not a planner result: the surface dose rate that"
                  " Curiosity's RAD instrument measured in Gale Crater (Hassler et al. 2014, galactic cosmic rays only,"
                  " solar particle events excluded), scaled to the planned time outside. It is not a measurement at"
                  " Jezero and not a forecast; Jezero sits higher than Gale, so its dose is likely somewhat higher."
                  " It does not change the route or the time margin.")
        source_ids, refs = [], []
    elif topic == "limits":
        lead = ("This is not a safety assessment. The planner covers only terrain slope against the chosen ceiling,"
                " cells with no elevation data, distance and a constant walking speed on 20 m orbital terrain."
                " It cannot see rocks, sand, ripples or anything smaller than about 20 m.")
        body = " ".join(_assessment_text(name, item, budget, budget_label) for name, item in items.items())
        answer = f"{lead} {body}{CAVEAT}"
        source_ids = list(context["sourceIds"])
        refs = [f"{name}.{field}" for name in items for field in ("status", "marginMin")]
    else:
        lead = (f"Scenario at the current position, with {_n(budget, 'min')} of remaining time." if rehearsal
                else f"Round trip from the hypothetical base to {stop_name} under a slope ceiling of"
                     f" {_n(inputs.get('maxSlopeDeg'), 'degrees')}.")
        body = " ".join(_assessment_text(name, item, budget, budget_label) for name, item in items.items())
        slopes = "".join(_slope_text(item) for item in items.values()) if topic == "route" else ""
        answer = f"{lead} {body}{slopes}{CAVEAT}"
        source_ids = list(context["sourceIds"])
        refs = [f"{name}.{field}" for name in items for field in ("status", "totalRequiredMin", "marginMin")
                + (("longestOutOfContactMin", "contactStatus") if items[name].get("contactStatus") else ())]

    facts = {"destination": stop_name, "inputs": {k: v for k, v in inputs.items() if isinstance(v, (int, float, str))},
             "assessments": {name: {**{f: item.get(f) for f in FIELDS},
                                    **{leg: {f: item[leg].get(f) for f in LEG_FIELDS} for leg in LEGS if item.get(leg)}}
                             for name, item in items.items()},
             "stop": {k: stop.get(k) for k in ("description", "samples", "locationProvenance", "scientificQuestion")},
             "sources": [{k: known[i].get(k) for k in ("sourceId", "title", "resolution", "limitations")}
                         for i in allowed_sources if i in known]}
    traced = topic in ("route", "return", "limits")  # answers made of planner numbers carry a proof strip
    result = {"answer": answer, "sourceIds": source_ids, "metricRefs": refs, "mode": "template",
              "supported": topic != "unsupported", "modelVersion": context["modelVersion"],
              "tracedNumbers": _trace(answer, facts) if traced else None}
    if complete is None and os.environ.get("MODEL_API_KEY") and os.environ.get("MODEL_PROVIDER", "anthropic") in ("", "anthropic"):
        complete = anthropic_complete
    if complete is None or topic in ("unsupported", "radiation", "limits"):  # fixed wording, never rephrased by a model
        return result

    facts["referenceAnswer"] = answer
    try:
        text = complete(json.dumps({"question": question, "facts": facts, "allowedSourceIds": allowed_sources,
                                    "allowedMetricRefs": allowed_refs}, allow_nan=False))
        reply = json.loads(text[text.index("{"):text.rindex("}") + 1])
        generated = reply["answer"]
        if (isinstance(generated, str) and generated.strip() and len(generated.split()) <= 160
                and set(reply["sourceIds"]) <= set(allowed_sources) and set(reply["metricRefs"]) <= set(allowed_refs)
                and _consistent(generated, _numbers(facts))):
            return {**result, "answer": generated.strip(), "sourceIds": list(reply["sourceIds"]),
                    "metricRefs": list(reply["metricRefs"]), "mode": "model",
                    "tracedNumbers": _trace(generated.strip(), facts) if traced else None}
    except Exception:  # provider outage, timeout, refusal or malformed output: the labelled template stands
        pass
    return result
