import json

from jsonschema import Draft202012Validator

from scripts.generate_fixtures import OUTPUT, generate
from server.export_schema import schema_text


def test_handoff_fixtures_match_runtime_and_schema(tmp_path):
    before = {p.name: p.read_text() for p in OUTPUT.glob("*.json")}
    generate(tmp_path)
    after = {p.name: p.read_text() for p in tmp_path.glob("*.json")}
    assert before == after, "Regenerate committed fixtures after changing the contract"
    schema = json.loads(schema_text())
    assert len(after) == 7
    for text in after.values():
        fixture = json.loads(text)
        assert fixture["synthetic"] is True
        model = "ErrorResponse" if fixture["httpStatus"] != 200 else (
            "RehearsalResponse" if fixture["endpoint"] == "/api/rehearse" else "PlanResponse")
        Draft202012Validator({"$ref": f"#/$defs/{model}", "$defs": schema["$defs"]}).validate(fixture["response"])
