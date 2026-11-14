import "./mission.css";
import { num } from "./format";
import type { Inputs, Mission } from "./state";
import { MODE_LABEL, type Mode } from "./types";

type NumberKey = "totalBudgetMin" | "maxSlopeDeg" | "speedMPerMin" | "dwellMin" | "reserveMin";

export function MissionControls({ m }: { m: Mission }) {
  const { state, dispatch } = m, { inputs, freshness, error } = state;
  const region = state.bundle!.region, bounds = region.parameterBounds;
  const locked = state.rehearsing, requesting = freshness === "requesting";
  const set = (key: keyof Inputs, value: string | number) => dispatch({ type: "setInput", key, value });

  const number = (key: NumberKey, label: string, unit: string, min?: number, max?: number, assumption = true) => (
    <div className="field">
      <label htmlFor={`in-${key}`}>{label} {assumption && <span className="tag">Assumption</span>}</label>
      <div className="with-unit">
        <input id={`in-${key}`} type="number" min={min} max={max} step="any" value={inputs[key]} disabled={locked}
          onChange={(e) => Number.isFinite(e.target.valueAsNumber) && set(key, e.target.valueAsNumber)} />
        <span className="unit">{unit}</span>
      </div>
    </div>
  );

  return (
    <form className="controls" onSubmit={(e) => { e.preventDefault(); m.requestRoutes(); }}>
      <h2 className="panel-heading">Excursion plan</h2>

      <div className="field">
        <label htmlFor="in-target">Destination</label>
        <select id="in-target" value={inputs.targetId} disabled={locked} onChange={(e) => set("targetId", e.target.value)}>
          {region.scienceStops.map((s) => <option key={s.id} value={s.id}>{s.name ?? s.id}</option>)}
        </select>
        <span className="caption">Source-backed stop</span>
      </div>

      <fieldset className="field modes" disabled={locked}>
        <legend>Route mode</legend>
        {(Object.keys(MODE_LABEL) as Mode[]).map((mode) => (
          <label key={mode}><input type="radio" name="mode" checked={inputs.mode === mode} onChange={() => set("mode", mode)} /> {MODE_LABEL[mode]}</label>
        ))}
      </fieldset>

      {number("totalBudgetMin", "Time budget", "min", 0)}

      <details className="assumptions">
        <summary>Assumptions (4)</summary>
        {number("maxSlopeDeg", "Slope ceiling", "°", bounds.maxSlopeDeg[0], bounds.maxSlopeDeg[1])}
        {number("speedMPerMin", "Travel speed", "m/min", 0, bounds.speedMPerMin[1])}
        {number("dwellMin", "Dwell at the stop", "min", 0)}
        {number("reserveMin", "Reserve", "min", 0)}
      </details>

      <p className="base">
        <span className="tag tag-hyp">Base · Hypothetical</span>{" "}
        {m.baseXY ? <span className="caption">x {num(m.baseXY[0])} m, y {num(m.baseXY[1])} m</span>
          : <span className="caption">This region defines no base, so routes cannot be requested.</span>}
      </p>

      {locked ? (
        <>
          <button type="button" className="btn" onClick={() => dispatch({ type: "rehearse", on: false })}>Edit plan</button>
          <p className="reason">Inputs are read-only during rehearsal.</p>
        </>
      ) : (
        <button type="submit" className="btn btn-primary" disabled={requesting || !m.baseXY}>Request routes</button>
      )}

      {requesting && (
        <div className="banner" role="status">
          <span>Requesting routes from the planning service…</span>
          <span className="indeterminate" aria-hidden="true" />
        </div>
      )}
      {state.expired && <div className="banner banner-outdated" role="alert">This plan has expired. Request routes again.</div>}
      {freshness === "outdated" && !state.expired && (
        <div className="banner banner-outdated" role="status">Inputs changed. These results no longer match.</div>
      )}
      {freshness === "none" && <p className="reason">Request routes to see the calculated round trip.</p>}
      {freshness === "failed" && error && (
        <div className="banner banner-error" role="alert">
          {error.status === "data_unavailable" ? (
            <>
              <span>The planning data for this region could not be loaded. {error.message}</span>
              <button type="button" className="btn" onClick={m.loadRegion}>Retry</button>
            </>
          ) : <span>{error.message}</span>}
        </div>
      )}
    </form>
  );
}
