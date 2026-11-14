import { useState } from "react";
import { STARTER_QUESTIONS, type Mission } from "../mission/state";
import { MODE_LABEL } from "../mission/types";
import "./assistant.css";

const ASSESSMENT: Record<string, string> = {
  ...MODE_LABEL, immediateReturn: "Return now", continueThenReturn: "Continue, then return",
};
const FIELD: Record<string, string> = {
  marginMin: "remaining margin", totalRequiredMin: "total time required", travelMin: "travel time estimate",
  totalDistanceM: "distance", distanceM: "distance", dwellMin: "dwell", reserveMin: "reserve", status: "status",
  maxSlopeDeg: "maximum slope", meanSlopeDeg: "mean slope", ascentM: "ascent",
};
const LEG: Record<string, string> = {
  outbound: "outbound", return: "return", currentToTarget: "to destination", targetToBase: "back to base",
};

/** "slope_penalized.outbound.maxSlopeDeg" → "Lower slope · outbound · maximum slope". Unknown parts are shown as sent. */
export function metricLabel(ref: string): string {
  const [head, ...rest] = ref.split(".");
  return [ASSESSMENT[head] ?? head, ...rest.map((part) => LEG[part] ?? FIELD[part] ?? part)].join(" · ");
}

export function MissionAssistant({ m }: { m: Mission }) {
  const { state, dispatch } = m;
  const { brief, bundle, plan, ret } = state;
  const [text, setText] = useState("");
  const reason = m.current ? null
    : state.expired ? "This plan has expired. Request routes again."
    : state.freshness === "outdated" ? "Results are outdated. Request routes again to enable."
    : "Request routes to enable.";
  const disabled = !m.current || brief.status === "loading";
  const title = (id: string) => bundle?.region.sources.find((s) => s.sourceId === id)?.title ?? id;

  return (
    <section className="assistant" aria-label="Mission assistant">
      <h2 className="panel-heading">Ask about this plan</h2>
      <p className="caption">The assistant explains the calculated plan. It cannot change routes, inputs or the map.</p>
      {m.current && plan && (
        <p className="caption">
          Explaining plan <span className="mono">{(ret.data?.planId ?? plan.planId).slice(0, 8)}</span>
          {ret.data && <> · current return scenario <span className="tag tag-hyp">Hypothetical</span></>}
        </p>
      )}

      <div className="as-starters">
        {STARTER_QUESTIONS.map((q) => (
          <button key={q} type="button" className="btn" disabled={disabled} onClick={() => m.ask(q)}>{q}</button>
        ))}
      </div>
      <form className="field" onSubmit={(e) => { e.preventDefault(); if (text.trim()) { m.ask(text); setText(""); } }}>
        <label htmlFor="as-question">Your question</label>
        <div className="as-ask">
          <input id="as-question" value={text} maxLength={500} disabled={disabled} autoComplete="off"
            onChange={(e) => setText(e.target.value)} />
          <button type="submit" className="btn btn-primary" disabled={disabled || !text.trim()}>Ask</button>
        </div>
      </form>
      {reason && <p className="reason">{reason}</p>}

      <div aria-live="polite">
        {brief.status === "loading" && <p className="status status-updating">Preparing explanation…</p>}
        {brief.status === "ok" && brief.data && (
          <article className={`card as-answer${brief.data.supported ? "" : " as-unsupported"}`}>
            <p className="as-question">{state.question}</p>
            <p className="as-mode">
              {brief.data.mode === "model" ? "AI model" : "Standard explanation"}
              {!brief.data.supported && " · outside the supplied evidence"}
            </p>
            <p className="prose as-text">{brief.data.answer}</p>
            {(brief.data.sourceIds.length > 0 || brief.data.metricRefs.length > 0) && (
              <div className="as-chips" aria-label="Sources and metrics cited">
                {brief.data.sourceIds.map((id) => (
                  <button key={id} type="button" className={`tag as-chip${state.highlight === id ? " highlight" : ""}`}
                    onClick={() => dispatch({ type: "setHighlight", ref: id })}>
                    <span aria-hidden="true">▤</span> <span className="sr-only">Source: </span>{title(id)}
                  </button>
                ))}
                {brief.data.metricRefs.map((ref) => (
                  <button key={ref} type="button" className={`tag as-chip${state.highlight === ref ? " highlight" : ""}`}
                    onClick={() => dispatch({ type: "setHighlight", ref })}>
                    <span aria-hidden="true">#</span> <span className="sr-only">Metric: </span>{metricLabel(ref)}
                  </button>
                ))}
              </div>
            )}
            <p className="caption">Authoritative numbers are in the Routes tab.</p>
          </article>
        )}
      </div>
      {brief.status === "error" && brief.error && (
        <p className="banner banner-error" role="alert">
          {brief.error.code === "plan_expired"
            ? "This plan has expired. Request routes again."
            : `No explanation is available: ${brief.error.message} The calculated numbers remain in the Routes tab.`}
        </p>
      )}
    </section>
  );
}
