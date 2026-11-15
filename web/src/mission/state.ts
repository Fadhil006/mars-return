// One reducer owns every piece of mission state; all views read the same plan.
import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";
import { ApiFailure, loadBundle, newRequestId, post } from "./api";
import { corridorPolygon, routePoints, type RoutePoint } from "./geo";
import type { Assessment, BriefResponse, Mode, PlanResponse, ReachResponse, RegionBundle, RehearsalResponse, StressResponse, XY } from "./types";

export type Freshness = "none" | "requesting" | "current" | "outdated" | "failed";
export type Tab = "routes" | "evidence" | "assistant";
export type LayerKey = "imagery" | "slope" | "stops" | "labels" | "traverse" | "envelope";
export type ChildKey = "ret" | "reach" | "stress" | "brief";

export interface Inputs {
  targetId: string;
  mode: Mode;
  totalBudgetMin: number;
  maxSlopeDeg: number;
  speedMPerMin: number;
  dwellMin: number;
  reserveMin: number;
}

export interface Fail { status: string; code: string; message: string }

export interface Async<T> {
  status: "idle" | "loading" | "ok" | "error";
  requestId: string | null;
  data: T | null;
  error: Fail | null;
}

export interface State {
  regionStatus: "loading" | "ok" | "error";
  regionError: Fail | null;
  bundle: RegionBundle | null;
  inputs: Inputs;
  freshness: Freshness;
  expired: boolean;
  requestId: string | null;
  plan: PlanResponse | null;
  planInputs: Inputs | null; // the inputs `plan` was calculated from
  error: Fail | null;
  rehearsing: boolean;
  posIndex: number;
  playing: boolean;
  scenario: { blocked: boolean; remainingMin: number | null }; // null = default for the current position
  ret: Async<RehearsalResponse>;
  reach: Async<ReachResponse>;
  stress: Async<StressResponse>;
  brief: Async<BriefResponse>;
  question: string;
  view: "2d" | "3d";
  layers: Record<LayerKey, boolean>;
  tab: Tab;
  reportOpen: boolean;
  highlight: string | null; // a metricRef or sourceId picked from an assistant citation
}

const idle = { status: "idle", requestId: null, data: null, error: null } as const;

export const initialState: State = {
  regionStatus: "loading", regionError: null, bundle: null,
  inputs: { targetId: "", mode: "shortest", totalBudgetMin: 180, maxSlopeDeg: 15, speedMPerMin: 30, dwellMin: 10, reserveMin: 20 },
  freshness: "none", expired: false, requestId: null, plan: null, planInputs: null, error: null,
  rehearsing: false, posIndex: 0, playing: false, scenario: { blocked: false, remainingMin: null },
  ret: idle, reach: idle, stress: idle, brief: idle, question: "",
  view: "2d", layers: { imagery: true, slope: false, stops: true, labels: true, traverse: false, envelope: true },
  tab: "evidence", reportOpen: false, highlight: null,
};

export type Action =
  | { type: "regionLoading" }
  | { type: "regionLoaded"; bundle: RegionBundle }
  | { type: "regionFailed"; error: Fail }
  | { type: "setInput"; key: keyof Inputs; value: string | number }
  | { type: "planRequested"; requestId: string }
  | { type: "planLoaded"; requestId: string; plan: PlanResponse; inputs: Inputs }
  | { type: "planFailed"; requestId: string; error: Fail }
  | { type: "rehearse"; on: boolean }
  | { type: "setPos"; index: number }
  | { type: "setPlaying"; playing: boolean }
  | { type: "setScenario"; blocked?: boolean; remainingMin?: number | null }
  | { type: "resetScenario" }
  | { type: "childRequested"; key: ChildKey; requestId: string; question?: string }
  | { type: "childLoaded"; key: ChildKey; requestId: string; data: unknown }
  | { type: "childFailed"; key: ChildKey; requestId: string; error: Fail }
  | { type: "setView"; view: "2d" | "3d" }
  | { type: "toggleLayer"; key: LayerKey }
  | { type: "setTab"; tab: Tab }
  | { type: "setReport"; open: boolean }
  | { type: "setHighlight"; ref: string | null };

// Scenario results and explanations never outlive the position or scenario they were asked about.
const clearScenarioResults = { ret: idle, reach: idle, brief: idle, highlight: null } as const;
const clearAll = { ...clearScenarioResults, stress: idle, rehearsing: false, playing: false, posIndex: 0,
  scenario: { blocked: false, remainingMin: null }, reportOpen: false } as const;

export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "regionLoading":
      return { ...s, regionStatus: "loading", regionError: null };
    case "regionLoaded": {
      const stops = a.bundle.region.scienceStops;
      const preset = a.bundle.region.manifest.scenario?.defaultTargetId;
      const targetId = stops.some((t) => t.id === preset) ? preset! : stops[0]?.id ?? "";
      return { ...initialState, regionStatus: "ok", bundle: a.bundle, inputs: { ...initialState.inputs, targetId } };
    }
    case "regionFailed":
      return { ...s, regionStatus: "error", regionError: a.error, bundle: null };
    case "setInput": {
      if (s.inputs[a.key] === a.value) return s;
      const inputs = { ...s.inputs, [a.key]: a.value } as Inputs;
      // Both modes are already in the plan, so choosing between them is not a new calculation.
      if (a.key === "mode" && s.freshness === "current" && s.planInputs)
        return { ...s, ...clearAll, inputs, planInputs: { ...s.planInputs, mode: inputs.mode } };
      const tab = a.key === "targetId" ? "evidence" : s.tab;
      // Any input change makes a shown result outdated at once; an in-flight request is abandoned.
      const freshness: Freshness = s.plan ? "outdated" : "none";
      return { ...s, ...clearAll, inputs, tab, freshness, requestId: null, error: null, expired: false };
    }
    case "planRequested":
      return { ...s, ...clearAll, freshness: "requesting", requestId: a.requestId, error: null, expired: false };
    case "planLoaded":
      if (a.requestId !== s.requestId) return s; // late response for an older request
      return { ...s, freshness: "current", plan: a.plan, planInputs: a.inputs, tab: "routes" };
    case "planFailed":
      if (a.requestId !== s.requestId) return s;
      // No stale success: the earlier route is removed, not left on screen as if current.
      return { ...s, freshness: "failed", plan: null, planInputs: null, error: a.error };
    case "rehearse":
      if (a.on && s.freshness !== "current") return s;
      return { ...s, ...clearScenarioResults, rehearsing: a.on, playing: false, posIndex: 0,
        scenario: { blocked: false, remainingMin: null }, tab: a.on ? "routes" : s.tab };
    case "setPos":
      if (a.index === s.posIndex) return s;
      return { ...s, ...clearScenarioResults, posIndex: a.index, scenario: { ...s.scenario, remainingMin: null } };
    case "setPlaying":
      return { ...s, playing: a.playing };
    case "setScenario":
      return { ...s, ...clearScenarioResults, playing: false, scenario: { ...s.scenario,
        ...(a.blocked === undefined ? {} : { blocked: a.blocked }),
        ...(a.remainingMin === undefined ? {} : { remainingMin: a.remainingMin }) } };
    case "resetScenario":
      return { ...s, ...clearScenarioResults, playing: false, scenario: { blocked: false, remainingMin: null } };
    case "childRequested":
      if (s.freshness !== "current") return s;
      return { ...s, [a.key]: { status: "loading", requestId: a.requestId, data: null, error: null },
        ...(a.key === "brief" ? { question: a.question ?? "", highlight: null } : {}),
        ...(a.key === "ret" || a.key === "reach" ? { brief: idle, playing: false } : {}) };
    case "childLoaded":
      if (s[a.key].requestId !== a.requestId) return s;
      return { ...s, [a.key]: { status: "ok", requestId: a.requestId, data: a.data, error: null } };
    case "childFailed": {
      if (s[a.key].requestId !== a.requestId) return s;
      const next = { ...s, [a.key]: { status: "error", requestId: a.requestId, data: null, error: a.error } };
      // The server forgot the plan (restart, one-hour expiry or eviction): recalculation is required.
      return a.error.code === "plan_expired"
        ? { ...next, ...clearAll, freshness: "outdated", expired: true, requestId: null }
        : next;
    }
    case "setView":
      return { ...s, view: a.view };
    case "toggleLayer":
      return { ...s, layers: { ...s.layers, [a.key]: !s.layers[a.key] } };
    case "setTab":
      return { ...s, tab: a.tab };
    case "setReport":
      return a.open && s.freshness !== "current" ? s : { ...s, reportOpen: a.open };
    case "setHighlight":
      return { ...s, highlight: a.ref, tab: a.ref ? (a.ref.includes(".") ? "routes" : "evidence") : s.tab };
  }
}

/** Values every view needs, derived from returned data only. */
export function derive(s: State) {
  const current = s.freshness === "current" && !!s.plan;
  const mode = s.planInputs?.mode ?? s.inputs.mode;
  const assessment: Assessment | null = s.plan ? s.plan.options[mode] : null;
  const points: RoutePoint[] = routePoints(assessment);
  const posIndex = Math.min(s.posIndex, Math.max(points.length - 1, 0));
  const point: RoutePoint | null = points[posIndex] ?? null;
  const corridor: XY[] | null = s.rehearsing && s.scenario.blocked ? corridorPolygon(points, posIndex) : null;
  // Scenario inputs sent to the service, not results: time elapsed at this playback position under the plan's speed and dwell.
  const p = s.planInputs;
  const elapsedMin = p && point ? point.alongM / p.speedMPerMin + (point.leg === "return" ? p.dwellMin : 0) : 0;
  const defaultRemainingMin = p ? Math.max(0, Math.round((p.totalBudgetMin - elapsedMin) * 10) / 10) : 0;
  const remainingMin = s.scenario.remainingMin ?? defaultRemainingMin;
  const stop = s.bundle?.region.scienceStops.find((t) => t.id === s.inputs.targetId) ?? null;
  const baseXY = s.bundle?.region.manifest.scenario?.baseXY ?? null;
  return { current, mode, assessment, points, posIndex, point, corridor, elapsedMin, defaultRemainingMin, remainingMin, stop, baseXY };
}

export const STARTER_QUESTIONS = ["Why this route?", "Can I still return?", "What evidence supports this destination?"] as const;

const fail = (e: unknown): Fail => e instanceof ApiFailure
  ? { status: e.status, code: e.code, message: e.message }
  : { status: "data_unavailable", code: "client_error", message: String(e) };

export function useMission() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const ref = useRef(state);
  ref.current = state;
  const d = useMemo(() => derive(state), [state]);
  const dRef = useRef(d);
  dRef.current = d;

  const loadRegion = useCallback(() => {
    dispatch({ type: "regionLoading" });
    loadBundle().then((bundle) => dispatch({ type: "regionLoaded", bundle }),
      (e) => dispatch({ type: "regionFailed", error: fail(e) }));
  }, []);
  useEffect(loadRegion, [loadRegion]);

  const identity = () => {
    const s = ref.current, m = s.bundle!.region.manifest;
    return { requestId: newRequestId(), schemaVersion: 1, datasetVersion: m.datasetVersion, baseXY: m.scenario!.baseXY };
  };

  const compared = useRef(false); // once routes have been compared, picking a site on the map re-plans straight away
  const requestRoutes = useCallback((patch: Partial<Inputs> = {}) => {
    const s = ref.current;
    if (!s.bundle?.region.manifest.scenario) return;
    compared.current = true;
    const inputs = { ...s.inputs, ...patch };
    const { mode, ...rest } = inputs;
    const body = { ...identity(), ...rest };
    dispatch({ type: "planRequested", requestId: body.requestId });
    post<PlanResponse>("plan", body).then(
      (plan) => dispatch({ type: "planLoaded", requestId: body.requestId, plan, inputs }),
      (e) => dispatch({ type: "planFailed", requestId: body.requestId, error: fail(e) }));
  }, []);

  const child = useCallback((key: ChildKey, endpoint: "rehearse" | "reach" | "stress" | "brief", body: { requestId: string } & Record<string, unknown>, question?: string) => {
    dispatch({ type: "childRequested", key, requestId: body.requestId, question });
    post<unknown>(endpoint, body).then(
      (data) => dispatch({ type: "childLoaded", key, requestId: body.requestId, data }),
      (e) => dispatch({ type: "childFailed", key, requestId: body.requestId, error: fail(e) }));
  }, []);

  const scenarioBody = () => {
    const p = ref.current.planInputs!, x = dRef.current;
    return { ...identity(), maxSlopeDeg: p.maxSlopeDeg, speedMPerMin: p.speedMPerMin, reserveMin: p.reserveMin,
      blockedPolygonsXY: x.corridor ? [x.corridor] : [], selectedRouteMode: p.mode, remainingBudgetMin: x.remainingMin };
  };

  const requestReturn = useCallback(() => {
    const p = ref.current.planInputs, x = dRef.current;
    if (!p || !x.point) return;
    child("ret", "rehearse", { ...scenarioBody(), targetId: p.targetId, currentXY: x.point.xy, elapsedMin: x.elapsedMin,
      remainingDwellMin: x.point.leg === "outbound" ? p.dwellMin : 0 });
  }, [child]);

  const requestReach = useCallback(() => {
    if (ref.current.planInputs) child("reach", "reach", scenarioBody());
  }, [child]);

  const requestStress = useCallback(() => {
    const p = ref.current.planInputs;
    if (!p) return;
    const { mode, ...rest } = p;
    child("stress", "stress", { ...identity(), ...rest, selectedRouteMode: mode });
  }, [child]);

  const ask = useCallback((question: string) => {
    const s = ref.current, text = question.trim();
    if (!s.plan || !s.planInputs || !text) return;
    // After a scenario request the explanation is about that saved return assessment, not the original plan.
    child("brief", "brief", { requestId: newRequestId(), planId: s.ret.data?.planId ?? s.plan.planId,
      selectedRouteMode: s.planInputs.mode, question: text.slice(0, 500) }, text);
  }, [child]);

  /** Map click on a science stop: set it as the destination and, after the first comparison, show the route to it. */
  const pickStop = useCallback((targetId: string) => {
    dispatch({ type: "setInput", key: "targetId", value: targetId });
    if (compared.current) requestRoutes({ targetId });
  }, [requestRoutes]);

  return { state, ...d, dispatch, loadRegion, requestRoutes, pickStop, requestReturn, requestReach, requestStress, ask };
}

export type Mission = ReturnType<typeof useMission>;
