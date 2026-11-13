"""Generate shared schema from runtime models; --check detects drift."""

import argparse
import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from server.models import (ErrorResponse, PlanRequest, PlanResponse, ReachRequest, ReachResponse, RehearsalRequest,
                           RehearsalResponse, RegionResponse, StressRequest, StressResponse)

OUTPUT = Path(__file__).resolve().parents[1] / "shared/schema.json"


def schema_text():
    models = [PlanRequest, PlanResponse, RehearsalRequest, RehearsalResponse, ReachRequest, ReachResponse,
              StressRequest, StressResponse, RegionResponse, ErrorResponse]
    _, schema = models_json_schema([(model, "validation") for model in models], title="Mars Return API v1")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return json.dumps(schema, indent=2, allow_nan=False) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = schema_text()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            raise SystemExit("shared/schema.json is stale; run python -m server.export_schema")
    else:
        OUTPUT.write_text(text)
