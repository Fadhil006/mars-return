"""Version-one API definitions. Export with python -m server.export_schema."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Finite = Annotated[float, Field(allow_inf_nan=False, strict=True)]
Nonnegative = Annotated[Finite, Field(ge=0, le=1000000)]
XY = tuple[Finite, Finite]
Mode = Literal["shortest", "slope_penalized"]
Status = Literal["ok", "over_budget", "no_path", "invalid_input", "data_unavailable"]
Identifier = Annotated[str, Field(min_length=1, max_length=128)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Scenario(Model):
    requestId: Identifier
    schemaVersion: Literal[1]
    datasetVersion: Identifier
    baseXY: XY
    maxSlopeDeg: Annotated[Finite, Field(ge=5, le=30)] = 15
    speedMPerMin: Annotated[Finite, Field(gt=0, le=1000)] = 30
    reserveMin: Nonnegative = 20
    # Hypothetical contact scenario: mast on the base, eye height of the walker, and the longest time allowed out of sight.
    mastHeightM: Annotated[Finite, Field(ge=0, le=30)] = 2
    eyeHeightM: Annotated[Finite, Field(ge=0, le=3)] = 1.7
    maxOutOfContactMin: Annotated[Finite, Field(ge=0, le=600)] = 15
    blockedPolygonsXY: Annotated[list[list[XY]], Field(max_length=16)] = []

    @model_validator(mode="after")
    def polygons(self):
        for polygon in self.blockedPolygonsXY:
            if not 3 <= len(polygon) <= 128:
                raise ValueError("Each polygon requires 3–128 vertices")
            vertices = polygon[:-1] if polygon[0] == polygon[-1] else polygon
            if len(set(vertices)) < 3:
                raise ValueError("Polygon requires three distinct vertices")
            area = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(vertices, vertices[1:]+vertices[:1]))
            if not math.isfinite(area) or abs(area) < 1e-9:
                raise ValueError("Polygon must have nonzero finite area")
        return self


class Constraints(Scenario):
    targetId: Identifier


class PlanRequest(Constraints):
    totalBudgetMin: Nonnegative = 180
    dwellMin: Nonnegative = 10

    @model_validator(mode="after")
    def reserve_fits(self):
        if self.reserveMin > self.totalBudgetMin:
            raise ValueError("reserveMin cannot exceed totalBudgetMin")
        return self


class RehearsalRequest(Constraints):
    selectedRouteMode: Mode
    currentXY: XY
    elapsedMin: Nonnegative
    remainingBudgetMin: Nonnegative
    remainingDwellMin: Nonnegative = 10


class ReachRequest(Scenario):
    selectedRouteMode: Mode
    remainingBudgetMin: Nonnegative


class StressRequest(PlanRequest):
    selectedRouteMode: Mode
    closureRadiusM: Annotated[Finite, Field(ge=20, le=300)] = 60
    closureCount: Annotated[int, Field(ge=1, le=12)] = 8


class ProfileSample(Model):
    distanceM: Finite
    elevationM: Finite
    slopeDeg: Finite


class Leg(Model):
    status: Status
    pathXY: list[XY] | None
    distanceM: Finite | None
    ascentM: Finite | None
    maxSlopeDeg: Finite | None
    meanSlopeDeg: Finite | None
    profile: list[ProfileSample] | None
    travelMin: Finite | None = None
    cost: Finite | None = None
    requestedStartXY: XY | None = None
    requestedGoalXY: XY | None = None
    effectiveStartXY: XY | None = None
    effectiveGoalXY: XY | None = None
    outOfContactM: Finite | None = None
    outOfContactMin: Finite | None = None
    longestOutOfContactMin: Finite | None = None
    longestOutOfContactStartM: Finite | None = None
    longestOutOfContactEndM: Finite | None = None
    inContact: list[bool] | None = None
    message: str | None = None


class Assessment(Model):
    status: Status
    outbound: Leg | None = None
    return_: Leg | None = Field(default=None, alias="return")
    currentToTarget: Leg | None = None
    targetToBase: Leg | None = None
    totalDistanceM: Finite | None
    travelMin: Finite | None
    dwellMin: Finite
    reserveMin: Finite
    totalRequiredMin: Finite | None
    marginMin: Finite | None
    outOfContactMin: Finite | None = None
    longestOutOfContactMin: Finite | None = None
    maxOutOfContactMin: Finite | None = None
    contactStatus: Literal["within_rule", "exceeds_rule"] | None = None
    message: str | None = None


class Envelope(Model):
    requestId: Identifier
    schemaVersion: Literal[1] = 1
    datasetVersion: Identifier
    modelVersion: str = "grid-constant-speed-v1"
    planId: Identifier
    inputHash: str
    sourceIds: list[str]
    warnings: list[str]


class RouteOptions(Model):
    shortest: Assessment
    slope_penalized: Assessment


class Contact(Model):
    visible: list[list[Literal[0, 1]]]
    visibleFraction: Finite
    mastHeightM: Finite
    eyeHeightM: Finite
    maxOutOfContactMin: Finite


class PlanResponse(Envelope):
    options: RouteOptions
    contact: Contact | None = None


class RehearsalResponse(Envelope):
    selectedRouteMode: Mode
    immediateReturn: Assessment
    continueThenReturn: Assessment


class ReachResponse(Envelope):
    selectedRouteMode: Mode
    status: Status
    returnMin: list[list[Finite | None]]
    allowanceMin: Finite
    reachableAreaM2: Finite
    returnableAreaM2: Finite
    farthestReturnableMin: Finite | None


class Closure(Model):
    centerXY: XY
    alongReturnM: Finite
    status: Status
    returnDistanceM: Finite | None
    detourM: Finite | None
    totalRequiredMin: Finite | None
    marginMin: Finite | None
    pathXY: list[XY] | None


class StressResponse(Envelope):
    selectedRouteMode: Mode
    baseline: Assessment
    closures: list[Closure]
    closureRadiusM: Finite
    survivableCount: int
    worstMarginMin: Finite | None
    verdict: Literal["robust", "fragile", "unavailable"]


class BriefRequest(Model):
    requestId: Identifier
    schemaVersion: Literal[1] = 1
    planId: Identifier
    selectedRouteMode: Mode
    question: Annotated[str, Field(min_length=1, max_length=500)]


class BriefResponse(Model):
    requestId: Identifier
    schemaVersion: Literal[1] = 1
    planId: Identifier
    datasetVersion: Identifier
    modelVersion: str
    answer: str
    sourceIds: list[str]
    metricRefs: list[str]
    mode: Literal["model", "template"]
    supported: bool


class RegionManifest(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    width: Annotated[int, Field(ge=1, le=512)]
    height: Annotated[int, Field(ge=1, le=512)]
    cellSizeM: Annotated[Finite, Field(gt=0)]
    originXY: XY
    datasetVersion: Identifier


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")
    sourceId: Identifier
    title: str
    url: str


class ScienceStop(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    id: Identifier
    positionXY: XY
    sourceIds: list[str] = []


class RegionResponse(Model):
    schemaVersion: Literal[1] = 1
    datasetVersion: Identifier
    manifest: RegionManifest
    scienceStops: list[ScienceStop]
    sources: list[SourceRecord]
    layers: dict[str, str]
    parameterBounds: dict
    warnings: list[str]


class ErrorDetail(Model):
    code: str
    message: str


class ErrorResponse(Model):
    requestId: str | None = None
    schemaVersion: Literal[1] = 1
    status: Status
    error: ErrorDetail
