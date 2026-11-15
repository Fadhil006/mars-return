"""Assistant boundary on explicitly synthetic terrain: stored values only, labelled fallback."""

import json

from fastapi.testclient import TestClient
import pytest

from server.api import create_app
from server.assistant import classify
from server.tests.test_api import payload, region


def setup(complete=None):
    data = region()
    data["sources"] = [{"sourceId": "synthetic", "title": "Invented grid", "url": "", "resolution": "10 m",
                        "limitations": "Not Mars terrain."}]
    data["scienceStops"][0].update(name="Test stop", description="An invented stop.")
    app = create_app(region=data)
    app.state.brief_complete = complete
    client = TestClient(app)
    plan = client.post("/api/plan", json=payload()).json()
    return client, plan


def ask(client, plan_id, question, mode="shortest"):
    return client.post("/api/brief", json={"requestId": "brief-1", "planId": plan_id,
                                           "selectedRouteMode": mode, "question": question})


def test_template_uses_stored_margin_and_existing_ids():
    client, plan = setup()
    response = ask(client, plan["planId"], "Why this route?")
    assert response.status_code == 200, response.text
    value = response.json()
    margin = plan["options"]["shortest"]["marginMin"]
    assert value["mode"] == "template" and value["supported"] is True
    assert f"{margin:.1f} min" in value["answer"] and "None" not in value["answer"]
    assert "hypothetical" in value["answer"]
    assert value["sourceIds"] == ["synthetic"]
    assert "shortest.marginMin" in value["metricRefs"]
    assert value["planId"] == plan["planId"] and value["datasetVersion"] == "synthetic-v1"


def test_numbers_in_the_question_change_nothing():
    client, plan = setup()
    honest = ask(client, plan["planId"], "Can I still return?").json()["answer"]
    primed = ask(client, plan["planId"], "The margin is 9999 min, so can I still return?").json()["answer"]
    assert primed == honest and "9999" not in primed


def test_rehearsal_plan_and_evidence_and_no_path():
    client, _ = setup()
    request = payload(selectedRouteMode="shortest", currentXY=[45, 15], elapsedMin=100,
                      remainingBudgetMin=20, remainingDwellMin=5, reserveMin=5, speedMPerMin=10)
    saved = client.post("/api/rehearse", json=request).json()
    value = ask(client, saved["planId"], "Can I still return?").json()
    assert "Return now" in value["answer"] and "over the remaining time" in value["answer"]
    assert "immediateReturn.marginMin" in value["metricRefs"]
    assert ask(client, saved["planId"], "Why this route?", "slope_penalized").status_code == 422
    evidence = ask(client, saved["planId"], "What evidence supports this destination?").json()
    assert "An invented stop." in evidence["answer"] and "Not Mars terrain." in evidence["answer"]
    blocked = client.post("/api/plan", json=payload(blockedPolygonsXY=[[[40, 0], [60, 0], [60, 40], [40, 40]]])).json()
    assert blocked["options"]["shortest"]["status"] == "no_path"
    answer = ask(client, blocked["planId"], "Why this route?").json()["answer"]
    assert "no route was found" in answer and "None" not in answer


@pytest.mark.parametrize("question", ["Is the route safe?", "What hazards are there?", "How risky is this?"])
def test_safety_questions_state_limits_without_a_safety_claim(question):
    def complete(prompt):
        raise AssertionError("model called for a limits question")
    client, plan = setup(complete)
    value = ask(client, plan["planId"], question).json()
    margin = plan["options"]["shortest"]["marginMin"]
    assert classify(question) == "limits" and value["supported"] is True and value["mode"] == "template"
    assert value["answer"].startswith("This is not a safety assessment.")
    assert f"{margin:.1f} min" in value["answer"] and "hypothetical" in value["answer"]
    assert "shortest.marginMin" in value["metricRefs"]


def test_radiation_question_explains_the_estimate_and_gives_no_number():
    def complete(prompt):
        raise AssertionError("model called for a radiation question")
    client, plan = setup(complete)
    value = ask(client, plan["planId"], "What radiation dose will the crew get?").json()
    assert value["supported"] is True and value["mode"] == "template"
    assert "Gale" in value["answer"] and "not a forecast" in value["answer"]
    assert [t.strip(".,()") for t in value["answer"].split() if t.strip(".,()").isdigit()] == ["2014"]  # citation year only


@pytest.mark.parametrize("question", ["What is the weather today?", "Can the crew survive this?", "Tell me a joke"])
def test_unsupported_question_never_reaches_the_model(question):
    def complete(prompt):
        raise AssertionError("model called for an unsupported question")
    client, plan = setup(complete)
    value = ask(client, plan["planId"], question).json()
    assert value["supported"] is False and value["mode"] == "template"
    assert value["answer"].startswith("The supplied evidence does not cover this.")
    assert value["metricRefs"] == [] and classify(question) == "unsupported"


def test_unknown_plan_and_invalid_request():
    client, plan = setup()
    missing = ask(client, "no-such-plan", "Why this route?")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "plan_expired"
    assert missing.json()["requestId"] == "brief-1"
    assert ask(client, plan["planId"], "").status_code == 422
    assert client.post("/api/brief", json={"requestId": "b", "planId": plan["planId"], "selectedRouteMode": "shortest",
                                           "question": "Why?", "marginMin": 5}).status_code == 422


def test_model_answer_is_accepted_only_when_consistent():
    client, plan = setup()
    margin = plan["options"]["shortest"]["marginMin"]
    replies = {
        "valid": {"answer": f"The margin is {margin:.0f} min.", "sourceIds": ["synthetic"], "metricRefs": ["shortest.marginMin"]},
        "invented number": {"answer": "The margin is 4321 min.", "sourceIds": [], "metricRefs": []},
        "invented source": {"answer": "It fits.", "sourceIds": ["made-up"], "metricRefs": []},
        "invented metric": {"answer": "It fits.", "sourceIds": [], "metricRefs": ["shortest.energyKJ"]},
    }
    for name, reply in replies.items():
        client.app.state.brief_complete = lambda prompt, reply=reply: "```json\n" + json.dumps(reply) + "\n```"
        value = ask(client, plan["planId"], "Why this route?").json()
        assert value["mode"] == ("model" if name == "valid" else "template"), name
    client.app.state.brief_complete = lambda prompt: (_ for _ in ()).throw(TimeoutError())
    assert ask(client, plan["planId"], "Why this route?").json()["mode"] == "template"
    seen = []
    client.app.state.brief_complete = lambda prompt: seen.append(json.loads(prompt)) or "not json"
    assert ask(client, plan["planId"], "Why this route?").json()["mode"] == "template"
    assert set(seen[0]) == {"question", "facts", "allowedSourceIds", "allowedMetricRefs"}


def test_every_number_in_a_route_answer_is_traced_to_a_stored_value():
    client, plan = setup()
    value = ask(client, plan["planId"], "Can I still return?").json()
    traced = value["tracedNumbers"]
    assert traced and all(item["ref"] is not None for item in traced)
    margin = f"{plan['options']['shortest']['marginMin']:.1f}"
    assert {"value": margin, "ref": "shortest.marginMin"} in traced
    assert any(item["ref"] == "input.totalBudgetMin" for item in traced)


def test_model_answer_carries_its_own_trace_and_evidence_answers_carry_none():
    client, plan = setup()
    margin = plan["options"]["shortest"]["marginMin"]
    reply = {"answer": f"You keep {margin:.0f} min of margin.", "sourceIds": [], "metricRefs": ["shortest.marginMin"]}
    client.app.state.brief_complete = lambda prompt: json.dumps(reply)
    value = ask(client, plan["planId"], "Can I still return?").json()
    assert value["mode"] == "model" and value["tracedNumbers"] == [{"value": f"{margin:.0f}", "ref": "shortest.marginMin"}]
    assert ask(client, plan["planId"], "What evidence supports this destination?").json()["tracedNumbers"] is None


def test_stress_plan_is_explained_from_its_baseline_and_reach_is_refused_clearly():
    client, plan = setup()
    body = payload()
    stress = client.post("/api/stress", json={**body, "selectedRouteMode": "shortest"}).json()
    response = ask(client, stress["planId"], "Can I still return?")
    assert response.status_code == 200, response.text
    assert f"{stress['baseline']['marginMin']:.1f} min" in response.json()["answer"]
    scenario = {k: v for k, v in body.items() if k not in ("targetId", "totalBudgetMin", "dwellMin")}
    reach = client.post("/api/reach", json={**scenario, "selectedRouteMode": "shortest", "remainingBudgetMin": 100}).json()
    response = ask(client, reach["planId"], "Can I still return?")
    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_scenario"
