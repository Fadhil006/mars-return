// Mirrors shared/schema.json (server/models.py). Units: metres, minutes, degrees, m/min.
export type XY = [number, number];
export type Mode = "shortest" | "slope_penalized";
export type Status = "ok" | "over_budget" | "no_path" | "invalid_input" | "data_unavailable";

export const MODE_LABEL: Record<Mode, string> = {
  shortest: "Shortest distance",
  slope_penalized: "Lower slope",
};

export interface ProfileSample { distanceM: number; elevationM: number; slopeDeg: number }

export interface Leg {
  status: Status;
  pathXY: XY[] | null;
  distanceM: number | null;
  ascentM: number | null;
  maxSlopeDeg: number | null;
  meanSlopeDeg: number | null;
  profile: ProfileSample[] | null;
  travelMin: number | null;
  message: string | null;
}

export interface Assessment {
  status: Status;
  outbound: Leg | null;
  return: Leg | null;
  currentToTarget: Leg | null;
  targetToBase: Leg | null;
  totalDistanceM: number | null;
  travelMin: number | null;
  dwellMin: number;
  reserveMin: number;
  totalRequiredMin: number | null;
  marginMin: number | null;
  message: string | null;
}

export interface Envelope {
  requestId: string;
  schemaVersion: 1;
  datasetVersion: string;
  modelVersion: string;
  planId: string;
  inputHash: string;
  sourceIds: string[];
  warnings: string[];
}

export interface PlanResponse extends Envelope { options: Record<Mode, Assessment> }

export interface RehearsalResponse extends Envelope {
  selectedRouteMode: Mode;
  immediateReturn: Assessment;
  continueThenReturn: Assessment;
}

export interface ReachResponse extends Envelope {
  selectedRouteMode: Mode;
  status: Status;
  returnMin: (number | null)[][];
  allowanceMin: number;
  reachableAreaM2: number;
  returnableAreaM2: number;
  farthestReturnableMin: number | null;
}

export interface Closure {
  centerXY: XY;
  alongReturnM: number;
  status: Status;
  returnDistanceM: number | null;
  detourM: number | null;
  totalRequiredMin: number | null;
  marginMin: number | null;
  pathXY: XY[] | null;
}

export interface StressResponse extends Envelope {
  selectedRouteMode: Mode;
  baseline: Assessment;
  closures: Closure[];
  closureRadiusM: number;
  survivableCount: number;
  worstMarginMin: number | null;
  verdict: "robust" | "fragile" | "unavailable";
}

/** metricRefs are "<assessment>.<field>", e.g. "shortest.marginMin", "immediateReturn.marginMin". */
export interface BriefResponse {
  requestId: string;
  schemaVersion: 1;
  planId: string;
  datasetVersion: string;
  modelVersion: string;
  answer: string;
  sourceIds: string[];
  metricRefs: string[];
  mode: "model" | "template";
  supported: boolean;
}

export interface Manifest {
  width: number;
  height: number;
  cellSizeM: number;
  originXY: XY;
  datasetVersion: string;
  scenario?: { baseXY: XY; defaultTargetId: string; label: string };
  layerInfo?: Record<string, { resolutionM?: number; units?: string; validCells?: number }>;
  coverage?: Record<string, number>;
  slopeMethod?: string;
  maskMeaning?: string;
  warnings?: string[];
  [extra: string]: unknown;
}

export interface SourceRecord {
  sourceId: string;
  title: string;
  url: string;
  mission?: string;
  instrument?: string;
  publicationDate?: string | null;
  acquisitionDate?: string | null;
  downloaded?: string;
  resolution?: string;
  attribution?: string;
  limitations?: string;
  [extra: string]: unknown;
}

export interface Sample { number: number; name: string; type: string; sealedDate: string; sol: number; rockType: string | null }

export interface ScienceStop {
  id: string;
  positionXY: XY;
  sourceIds: string[];
  name?: string;
  kind?: string;
  description?: string;
  scientificQuestion?: string;
  locationProvenance?: string;
  locationUncertaintyM?: number | null;
  samples?: Sample[];
  roverSol?: number;
  roverElevationM?: number;
  [extra: string]: unknown;
}

export interface RegionResponse {
  schemaVersion: 1;
  datasetVersion: string;
  manifest: Manifest;
  scienceStops: ScienceStop[];
  sources: SourceRecord[];
  layers: Record<string, string>;
  parameterBounds: { maxSlopeDeg: [number, number]; speedMPerMin: [number, number] };
  warnings: string[];
}

export type Grid<T> = T[][]; // row-major, row 0 north, column 0 west

/** Region plus its assets. A layer that failed to load is null and named in `missing`. */
export interface RegionBundle {
  region: RegionResponse;
  elevation: Grid<number | null> | null;
  slope: Grid<number | null> | null;
  mask: Grid<boolean> | null;
  traverse: { pathXY: XY[]; waypoints: { sol: number; xy: XY }[] } | null;
  imageryUrl: string | null;
  missing: string[];
}
