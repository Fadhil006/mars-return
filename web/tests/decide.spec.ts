import { describe, expect, it } from "vitest";
import { callFeedback, passes } from "../src/mission/decide";
import { initialState, reducer, type State } from "../src/mission/state";
import type { Assessment, PlanResponse, RehearsalResponse } from "../src/mission/types";

const a = (over: Partial<Assessment>): Assessment => ({
  status: "ok", outbound: null, return: null, currentToTarget: null, targetToBase: null, totalDistanceM: 100,
  travelMin: 10, dwellMin: 0, reserveMin: 20, totalRequiredMin: 30, marginMin: 40, message: null, ...over,
});
const ret = (now: Partial<Assessment>, cont: Partial<Assessment>): RehearsalResponse => ({
  requestId: "r", schemaVersion: 1, datasetVersion: "v1", modelVersion: "m", planId: "p", inputHash: "h",
  sourceIds: [], warnings: [], selectedRouteMode: "shortest", immediateReturn: a(now), continueThenReturn: a(cont),
});

function rehearsing(): State {
  const plan = { requestId: "a", schemaVersion: 1, datasetVersion: "v1", modelVersion: "m", planId: "p", inputHash: "h",
    sourceIds: [], warnings: [], options: { shortest: a({}), slope_penalized: a({}) } } as PlanResponse;
  let s = reducer(initialState, { type: "planRequested", requestId: "a" });
  s = reducer(s, { type: "planLoaded", requestId: "a", plan, inputs: s.inputs });
  return reducer(s, { type: "childRequested", key: "ret", requestId: "r1" });
}

describe("decide first", () => {
  it("records exactly one call per return request, and a new request clears it", () => {
    let s = rehearsing();
    expect(s.call).toBeNull();
    s = reducer(s, { type: "makeCall", call: "continue" });
    expect(s.call).toBe("continue");
    expect(reducer(s, { type: "makeCall", call: "return" }).call).toBe("continue"); // first call stands
    s = reducer(s, { type: "childRequested", key: "ret", requestId: "r2" });
    expect(s.call).toBeNull();
  });

  it("ignores a call when no return options were requested", () => {
    const s = reducer(initialState, { type: "makeCall", call: "return" });
    expect(s.call).toBeNull();
  });

  it("names the planner's result for the chosen option and points to the one that passes", () => {
    const r = ret({ marginMin: 30, contactStatus: "within_rule" },
                  { marginMin: 12, contactStatus: "exceeds_rule", longestOutOfContactMin: 27, maxOutOfContactMin: 15 });
    expect(callFeedback("continue", r)).toBe("You chose continue, then return. The planner shows it fits the remaining time"
      + " with 12 min spare, but is out of sight of base for 27 min at a stretch, over the 15 min rule. Return now passes both checks.");
    expect(callFeedback("return", r)).toBe("You chose return now. The planner shows it fits the remaining time with 30 min spare"
      + " and stays within the contact rule.");
  });

  it("reports over-budget, silence and skip", () => {
    const r = ret({ marginMin: 5 }, { status: "over_budget", marginMin: -14 });
    expect(callFeedback("continue", r)).toContain("runs over the remaining time by 14 min. Return now passes both checks.");
    expect(callFeedback("none", r)).toMatch(/^No call made within 10 s\./);
    expect(callFeedback("skip", r)).toBeNull();
    expect(passes(a({ contactStatus: null }))).toBe(true);
  });
});
