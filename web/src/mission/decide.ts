// "Decide first": the user commits before the planner's options are shown (cognitive forcing; Buçinca et al. 2021).
// Feedback compares the call with returned statuses only; nothing is recalculated here.
import { hm } from "./format";
import type { Assessment, RehearsalResponse } from "./types";

export type Call = "return" | "continue" | "none" | "skip";
export const DECIDE_SECONDS = 10;

const LABEL = { return: "Return now", continue: "Continue, then return" } as const;

function outcome(a: Assessment): string {
  const time = a.status === "ok" ? `fits the remaining time with ${hm(a.marginMin)} spare`
    : a.status === "over_budget" ? `runs over the remaining time by ${hm(a.marginMin == null ? null : -a.marginMin)}`
    : "has no route";
  if (a.status !== "ok" || a.contactStatus == null) return time;
  return a.contactStatus === "exceeds_rule"
    ? `${time}, but is out of sight of base for ${hm(a.longestOutOfContactMin)} at a stretch, over the ${hm(a.maxOutOfContactMin)} rule`
    : `${time} and stays within the contact rule`;
}

/** Both checks pass: within time and, when reported, within the contact rule. */
export const passes = (a: Assessment) => a.status === "ok" && a.contactStatus !== "exceeds_rule";

/** One factual line about the user's call against the planner's two results; null when the user skipped. */
export function callFeedback(call: Call, ret: RehearsalResponse): string | null {
  if (call === "skip") return null;
  const now = ret.immediateReturn, cont = ret.continueThenReturn;
  if (call === "none") return `No call made within ${DECIDE_SECONDS} s. ${LABEL.return} ${outcome(now)}; ${LABEL.continue.toLowerCase()} ${outcome(cont)}.`;
  const [chosen, other, otherKey] = call === "return" ? [now, cont, "continue"] as const : [cont, now, "return"] as const;
  const tail = !passes(chosen) && passes(other) ? ` ${LABEL[otherKey]} passes both checks.` : "";
  return `You chose ${LABEL[call].toLowerCase()}. The planner shows it ${outcome(chosen)}.${tail}`;
}
