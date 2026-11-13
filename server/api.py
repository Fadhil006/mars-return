"""FastAPI service for the Group A Mars Return backend.

Endpoints
---------
GET  /api/region    regional manifest, layers, bounds, stops, sources
POST /api/plan      both route modes, round trip arithmetic, budget margin
POST /api/rehearse  immediate return vs continue-then-return
POST /api/brief     deterministic evidence-backed explanation of a stored plan
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from server.evidence import build_brief
from server.mission import (
    MODEL_VERSION,
    SCHEMA_VERSION,
    DataUnavailableError,
    Region,
    evaluate_plan,
    evaluate_rehearsal,
    load_region,
)

__all__ = ["PlanStore", "PlanLookupError", "ApiError", "create_app", "app"]

DEFAULT_TTL_SECONDS = 1800.0
DEFAULT_STORE_MAX = 256


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class _RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanRequest(_RequestModel):
    requestId: str = Field(min_length=1)
    schemaVersion: Literal[1]
    datasetVersion: str = Field(min_length=1)
    baseXY: tuple[float, float]
    targetId: str = Field(min_length=1)
    maxSlopeDeg: float = Field(ge=5, le=30)
    speedMPerMin: float = Field(ge=0)
    totalBudgetMin: float = Field(ge=0)
    reserveMin: float = Field(ge=0)
    dwellMin: float = Field(ge=0)
    blockedPolygonsXY: list[list[list[float]]] = Field(default_factory=list)


class RehearseRequest(_RequestModel):
    requestId: str = Field(min_length=1)
    schemaVersion: Literal[1]
    datasetVersion: str = Field(min_length=1)
    currentXY: tuple[float, float]
    elapsedMin: float = Field(ge=0)
    remainingBudgetMin: float = Field(ge=0)
    targetId: str = Field(min_length=1)
    baseXY: tuple[float, float]
    maxSlopeDeg: float = Field(ge=5, le=30)
    speedMPerMin: float = Field(ge=0)
    dwellMin: float = Field(ge=0)
    reserveMin: float = Field(ge=0)
    routeMode: Literal["shortest", "slope_penalized"] = "shortest"
    blockedPolygonsXY: list[list[list[float]]] = Field(default_factory=list)


class BriefRequest(_RequestModel):
    requestId: str = Field(min_length=1)
    planId: str = Field(min_length=1)
    selectedRouteMode: Literal["shortest", "slope_penalized"]
    question: str = Field(min_length=1, max_length=2000)


# ---------------------------------------------------------------------------
# Bounded in-memory plan store
# ---------------------------------------------------------------------------

class PlanLookupError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        plan_id: str | None = None,
        recalculate: bool = True,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.plan_id = plan_id
        self.recalculate = recalculate


class ApiError(RuntimeError):
    def __init__(
        self,
        status: str,
        code: str,
        message: str,
        status_code: int,
        *,
        plan_id: str | None = None,
        recalculate: bool = False,
        warnings: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.status_code = status_code
        self.plan_id = plan_id
        self.recalculate = recalculate
        self.warnings = warnings or []


@dataclass
class StoredPlan:
    plan_id: str
    input_hash: str
    model_version: str
    dataset_version: str
    plan: dict[str, Any]
    request: dict[str, Any]
    created_at: float
    expires_at: float


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class PlanStore:
    """Bounded LRU-ish store keyed by planId with explicit stale/expiry errors."""

    def __init__(self, *, ttl_seconds: float = DEFAULT_TTL_SECONDS, max_entries: int = DEFAULT_STORE_MAX) -> None:
        self.ttl_seconds = max(0.0, float(ttl_seconds))
        self.max_entries = max(1, int(max_entries))
        self._entries: OrderedDict[str, StoredPlan] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def put(self, plan: Mapping[str, Any], request: Mapping[str, Any]) -> StoredPlan:
        plan_id = str(plan.get("planId", ""))
        if not plan_id:
            raise ValueError("plan response has no planId")
        now = time.monotonic()
        entry = StoredPlan(
            plan_id=plan_id,
            input_hash=_canonical_hash(request),
            model_version=str(plan.get("modelVersion", "")),
            dataset_version=str(plan.get("datasetVersion", "")),
            plan=dict(plan),
            request=dict(request),
            created_at=now,
            expires_at=now + self.ttl_seconds,
        )
        self._entries[plan_id] = entry
        self._entries.move_to_end(plan_id)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)
        return entry

    def get(self, plan_id: str) -> StoredPlan:
        entry = self._entries.get(plan_id)
        if entry is None:
            raise PlanLookupError(
                "plan_not_found",
                f"No stored plan with planId {plan_id!r}. Recalculate the plan and try again.",
                404,
                plan_id=plan_id,
            )
        if time.monotonic() >= entry.expires_at:
            del self._entries[plan_id]
            raise PlanLookupError(
                "plan_expired",
                f"The stored plan {plan_id!r} has expired. Recalculate the plan and try again.",
                410,
                plan_id=plan_id,
            )
        self._entries.move_to_end(plan_id)
        return entry

    def hash_request(self, request: Mapping[str, Any]) -> str:
        return _canonical_hash(request)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def create_app(
    *,
    data_dir: str | None = None,
    plan_ttl_seconds: float | None = None,
    plan_store_max: int | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Mars Return API",
        version=MODEL_VERSION,
        description="Group A backend: terrain routing, mission budgets, rehearsals and briefs.",
    )
    app.state.region = None
    app.state.region_error = None
    app.state.data_dir = data_dir or os.environ.get("MARS_RETURN_DATA_DIR")
    app.state.plan_store = PlanStore(
        ttl_seconds=(
            plan_ttl_seconds
            if plan_ttl_seconds is not None
            else _env_float("MARS_RETURN_PLAN_TTL_SECONDS", DEFAULT_TTL_SECONDS)
        ),
        max_entries=(
            plan_store_max
            if plan_store_max is not None
            else _env_int("MARS_RETURN_PLAN_STORE_MAX", DEFAULT_STORE_MAX)
        ),
    )

    def get_region(request: Request) -> Region:
        region = request.app.state.region
        if region is not None:
            return region
        try:
            region = load_region(request.app.state.data_dir)
        except DataUnavailableError as exc:
            raise ApiError(
                "data_unavailable",
                "dataset_unavailable",
                f"Regional dataset is unavailable: {exc}",
                503,
            ) from exc
        request.app.state.region = region
        return region

    @app.exception_handler(ApiError)
    async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        body: dict[str, Any] = {
            "status": exc.status,
            "code": exc.code,
            "message": exc.message,
            "recalculate": exc.recalculate,
            "planId": exc.plan_id,
            "warnings": exc.warnings,
        }
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(PlanLookupError)
    async def _plan_error_handler(request: Request, exc: PlanLookupError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "invalid_input",
                "code": exc.code,
                "message": exc.message,
                "recalculate": exc.recalculate,
                "planId": exc.plan_id,
                "warnings": [],
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        warnings: list[dict[str, str]] = []
        for error in exc.errors():
            loc = ".".join(str(part) for part in error.get("loc", []))
            warnings.append(
                {
                    "code": "invalid_request",
                    "message": f"{loc}: {error.get('msg', 'invalid value')}",
                    "severity": "error",
                }
            )
        return JSONResponse(
            status_code=400,
            content={
                "status": "invalid_input",
                "code": "invalid_request",
                "message": "Request body failed schema validation.",
                "recalculate": False,
                "planId": None,
                "warnings": warnings,
            },
        )

    # -- endpoints -------------------------------------------------------
    @app.get("/api/region")
    def get_region_endpoint(request: Request) -> dict[str, Any]:
        region = get_region(request)
        return region.manifest

    @app.post("/api/plan")
    def plan_endpoint(payload: PlanRequest, request: Request) -> dict[str, Any]:
        region = get_region(request)
        body = payload.model_dump(mode="json")
        result = evaluate_plan(region, body)
        if result["status"] != "invalid_input":
            request.app.state.plan_store.put(result, body)
        return result

    @app.post("/api/rehearse")
    def rehearse_endpoint(payload: RehearseRequest, request: Request) -> dict[str, Any]:
        region = get_region(request)
        return evaluate_rehearsal(region, payload.model_dump(mode="json"))

    @app.post("/api/brief")
    def brief_endpoint(payload: BriefRequest, request: Request) -> dict[str, Any]:
        region = get_region(request)
        store: PlanStore = request.app.state.plan_store
        entry = store.get(payload.planId)

        if entry.model_version != region.model_version or entry.dataset_version != region.dataset_version:
            raise ApiError(
                "invalid_input",
                "plan_stale",
                (
                    f"Stored plan {payload.planId!r} was computed for "
                    f"model {entry.model_version!r}/dataset {entry.dataset_version!r}, "
                    f"but the service now runs model {region.model_version!r}/dataset "
                    f"{region.dataset_version!r}. Recalculate the plan."
                ),
                409,
                plan_id=payload.planId,
                recalculate=True,
            )

        if store.hash_request(entry.request) != entry.input_hash:
            raise ApiError(
                "invalid_input",
                "plan_integrity_error",
                f"Stored plan {payload.planId!r} failed its input-hash check. Recalculate the plan.",
                409,
                plan_id=payload.planId,
                recalculate=True,
            )

        if payload.selectedRouteMode not in entry.plan.get("routes", {}):
            raise ApiError(
                "invalid_input",
                "route_mode_unavailable",
                f"Stored plan {payload.planId!r} has no route mode {payload.selectedRouteMode!r}.",
                400,
                plan_id=payload.planId,
            )

        result = build_brief(region, entry.plan, entry.request, payload.selectedRouteMode)
        result["requestId"] = payload.requestId
        result["planId"] = payload.planId
        return result

    return app


app = create_app()
