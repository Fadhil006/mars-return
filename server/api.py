"""Mars Return API. Run from root: python -m uvicorn server.api:app."""

import logging
import os
from pathlib import Path
from threading import Lock
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from server.evidence import PlanStore
from server.models import PlanRequest, PlanResponse, RehearsalRequest, RehearsalResponse, RegionResponse
from server.region import load_region

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)
WARNINGS = [
    "Illustrative scenario, not certified astronaut navigation or physiological safety guidance.",
    "Constant speed and horizontal grid distance do not model terrain-dependent fatigue or suit performance.",
    "Endpoints are represented by containing-cell centers; paths are not smoothed.",
]


def error(status_code, status, code, message, request_id=None):
    return JSONResponse(status_code=status_code, content={"requestId": request_id, "schemaVersion": 1,
        "status": status, "error": {"code": code, "message": message}})


def create_app(region_dir=None, *, region=None, store=None):
    app = FastAPI(title="Mars Return", version="1.0.0")
    app.state.store = store if store is not None else PlanStore()
    app.state.region = region
    app.state.load_attempted = region is not None
    app.state.load_lock = Lock()
    configured = Path(region_dir or os.environ.get("REGION_DATA_DIR", "data/region"))
    app.state.region_dir = configured if configured.is_absolute() else ROOT / configured

    @app.middleware("http")
    async def limit_body(request, call_next):
        if request.method == "POST":
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 262144:
                    return error(413, "invalid_input", "request_too_large", "Maximum request size is 256 KiB")
            request._body = bytes(body)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc):
        identifier = exc.body.get("requestId") if isinstance(exc.body, dict) else None
        if not isinstance(identifier, str):
            identifier = None
        message = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return error(422, "invalid_input", "validation_error", message, identifier)

    def active_region():
        # The bundle is immutable for a running process; restart after replacing it.
        with app.state.load_lock:
            if not app.state.load_attempted:
                app.state.load_attempted = True
                try:
                    app.state.region = load_region(app.state.region_dir)
                except (OSError, ValueError, KeyError, TypeError):
                    LOGGER.warning("Prepared region unavailable or invalid")
        return app.state.region

    @app.get("/api/region", response_model=RegionResponse)
    def get_region():
        current = active_region()
        if current is None:
            return error(503, "data_unavailable", "region_unavailable", "Prepare and validate the region bundle, then restart")
        return {"schemaVersion": 1, "datasetVersion": current["manifest"]["datasetVersion"],
                "manifest": current["manifest"], "scienceStops": current["scienceStops"],
                "sources": current.get("sources", []),
                "layers": {name: f"/api/assets/{name}" for name in
                           ("imagery.webp", "elevation.json", "slope.json", "mask.json")},
                "parameterBounds": {"maxSlopeDeg": [5, 30], "speedMPerMin": [0, 1000],
                                    "speedMinimumExclusive": True},
                "warnings": WARNINGS + current["manifest"].get("warnings", [])}

    @app.get("/api/assets/{name}")
    def asset(name: str):
        current = active_region()
        if current is None:
            return error(503, "data_unavailable", "region_unavailable", "Region unavailable")
        if name not in ("imagery.webp", "elevation.json", "slope.json", "mask.json"):
            return error(404, "invalid_input", "asset_not_found", "Unknown region asset")
        path = Path(current.get("directory", app.state.region_dir)) / name
        if path.resolve().parent != path.parent.resolve():
            return error(503, "data_unavailable", "asset_unavailable", "Prepared asset escapes region directory")
        if not path.is_file():
            return error(503, "data_unavailable", "asset_unavailable", "Prepared asset missing")
        return FileResponse(path)

    def calculate(payload, rehearse=False):
        current = active_region()
        if current is None:
            return error(503, "data_unavailable", "region_unavailable", "Region unavailable", payload.requestId)
        if payload.datasetVersion != current["manifest"]["datasetVersion"]:
            return error(409, "invalid_input", "dataset_version_mismatch", "Reload the region and recalculate", payload.requestId)
        from server.mission import evaluate_plan, evaluate_rehearsal
        inputs = payload.model_dump(mode="json")
        start = perf_counter()
        try:
            result = (evaluate_rehearsal if rehearse else evaluate_plan)(current, inputs)
        except ValueError as exc:
            return error(422, "invalid_input", "invalid_scenario", str(exc), payload.requestId)
        assessments = [result["immediateReturn"], result["continueThenReturn"]] if rehearse else list(result["options"].values())
        invalid = next((item for item in assessments if item["status"] == "invalid_input"), None)
        if invalid is not None:
            return error(422, "invalid_input", "invalid_scenario",
                         invalid.get("message") or "Endpoint, destination, or scenario is invalid", payload.requestId)
        source_ids = sorted(set(s for stop in current["scienceStops"] for s in stop.get("sourceIds", [])) |
                            set(current["manifest"].get("sourceIds", [])))
        result.update(requestId=payload.requestId, schemaVersion=1, datasetVersion=payload.datasetVersion,
                      modelVersion="grid-constant-speed-v1", sourceIds=source_ids,
                      warnings=WARNINGS + current["manifest"].get("warnings", []))
        if rehearse:
            result["selectedRouteMode"] = payload.selectedRouteMode
        # Validate before persisting; B3 only sees trusted, serializable assessments.
        response_type = RehearsalResponse if rehearse else PlanResponse
        response_type.model_validate({**result, "planId": "pending", "inputHash": "pending"})
        plan_id, input_hash = app.state.store.save(inputs, result)
        LOGGER.info("mission evaluation kind=%s elapsed_ms=%.1f", "rehearse" if rehearse else "plan", (perf_counter()-start)*1000)
        return response_type.model_validate({**result, "planId": plan_id, "inputHash": input_hash})

    @app.post("/api/plan", response_model=PlanResponse, response_model_by_alias=True)
    def plan(payload: PlanRequest):
        return calculate(payload)

    @app.post("/api/rehearse", response_model=RehearsalResponse, response_model_by_alias=True)
    def rehearse(payload: RehearsalRequest):
        return calculate(payload, rehearse=True)

    return app


app = create_app()
