import { useLayoutEffect, useState, type ReactNode } from "react";
import "./mission.css";
import { hm, num } from "./format";
import type { Inputs, Mission } from "./state";

type NumberKey = "totalBudgetMin" | "maxSlopeDeg" | "speedMPerMin" | "dwellMin" | "reserveMin";

const svg = (d: ReactNode) => (
  <svg className="ico" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>
);
const ICON = {
  pin: svg(<><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" /><circle cx="12" cy="10" r="2.2" /></>),
  rover: svg(<><rect x="4" y="9" width="14" height="5" rx="1" /><path d="M8 9V6h5M18 11h2" /><circle cx="7" cy="17.5" r="1.8" /><circle cx="12" cy="17.5" r="1.8" /><circle cx="17" cy="17.5" r="1.8" /></>),
  slope: svg(<path d="M3 19h18L21 7z" />),
  clock: svg(<><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>),
  reserve: svg(<><rect x="3" y="7.5" width="16" height="9" rx="1.5" /><path d="M21 10.5v3M6.5 10.5v3M9.5 10.5v3" /></>),
  route: svg(<><circle cx="5" cy="18" r="2.2" /><circle cx="19" cy="6" r="2.2" /><path d="M7 17c4-1 2-6 6-7s3-2 4-3" /></>),
};

// "10 m" would read as metres, so short durations keep "min".
const dur = (v: number) => (Math.round(v) < 60 ? `${num(v)} min` : hm(v));

export function MissionControls({ m }: { m: Mission }) {
  const { state, dispatch } = m, { inputs, freshness, error } = state;
  const region = state.bundle!.region, bounds = region.parameterBounds;
  const locked = state.rehearsing, requesting = freshness === "requesting";
  const set = (key: keyof Inputs, value: string | number) => dispatch({ type: "setInput", key, value });
  const [editing, setEditing] = useState<NumberKey | null>(null);
  const stop = region.scienceStops.find((s) => s.id === inputs.targetId);
  // The field turns from formatted text into a number on focus; select it before the next keystroke so typing replaces the value.
  useLayoutEffect(() => { if (editing) (document.getElementById(`in-${editing}`) as HTMLInputElement | null)?.select(); }, [editing]);

  // Plain mono text that becomes a number input on focus; `show` formats the value when not being edited.
  const input = (key: NumberKey, label: string, min?: number, max?: number, show?: (v: number) => string) => {
    const formatted = show && editing !== key;
    return (
      <input id={`in-${key}`} className="plain" aria-label={label} type={formatted ? "text" : "number"} inputMode="decimal"
        min={min} max={max} step="any" value={formatted ? show(inputs[key]) : inputs[key]} readOnly={locked}
        onFocus={() => setEditing(key)} onBlur={() => setEditing(null)}
        onChange={(e) => Number.isFinite(e.target.valueAsNumber) && set(key, e.target.valueAsNumber)} />
    );
  };
  const row = (icon: ReactNode, key: NumberKey, label: string, unit: string, min?: number, max?: number, show?: (v: number) => string, extra?: ReactNode) => (
    <div className="arow">
      {icon}
      <label htmlFor={`in-${key}`}>{label}</label>
      <span className="aval">{input(key, `${label}, ${unit}`, min, max, show)}{!show && <span className="unit">{unit}</span>}{extra}</span>
    </div>
  );

  return (
    <form className="controls" onSubmit={(e) => { e.preventDefault(); m.requestRoutes(); }}>
      <h2 className="panel-heading">Excursion plan</h2>

      <div className="field dest">
        <label htmlFor="in-target">Destination</label>
        <select id="in-target" value={inputs.targetId} disabled={locked} onChange={(e) => set("targetId", e.target.value)}>
          {region.scienceStops.map((s) => <option key={s.id} value={s.id}>{s.name ?? s.id}</option>)}
        </select>
        <span className="caption">{ICON.pin}{stop?.kind === "rover_sample_site" ? "Perseverance sampling site" : "Source-backed stop"}</span>
      </div>

      <section className="assumptions" aria-labelledby="assumptions-h">
        <h3 id="assumptions-h" className="sub-heading">Assumptions <span className="tag">Assumption</span></h3>
        {row(ICON.rover, "speedMPerMin", "Traverse speed", "m/min", 0, bounds.speedMPerMin[1], undefined,
          <span className="caption derived">({num(inputs.speedMPerMin * 0.06, 2)} km/h)</span>)}
        {row(ICON.slope, "maxSlopeDeg", "Max slope (traverse)", "°", bounds.maxSlopeDeg[0], bounds.maxSlopeDeg[1])}
        {row(ICON.clock, "dwellMin", "On-site science time", "minutes", 0, undefined, dur)}
        {row(ICON.reserve, "reserveMin", "Reserve", "min", 0)}
      </section>

      <div className="budget">
        <label htmlFor="in-totalBudgetMin" className="sub-heading">Total time budget</label>
        {input("totalBudgetMin", "Total time budget, minutes", 0, undefined, dur)}
        <span className="caption">(outbound + on-site + return + reserve)</span>
      </div>

      <p className="base">
        <span className="tag tag-hyp">Base · Hypothetical</span>
        {!m.baseXY && <span className="caption"> This region defines no base, so routes cannot be requested.</span>}
      </p>

      <details className="advanced">
        <summary>Advanced assumptions</summary>
        {m.baseXY && <p className="caption">Hypothetical base at x {num(m.baseXY[0])} m, y {num(m.baseXY[1])} m</p>}
        <p className="caption">Parameter bounds: slope {bounds.maxSlopeDeg[0]}–{bounds.maxSlopeDeg[1]}°, speed up to {bounds.speedMPerMin[1]} m/min.</p>
        <h4 className="caption">Model limits ({region.warnings.length})</h4>
        <ul className="limits">{region.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
      </details>

      {locked ? (
        <>
          <button type="button" className="btn" onClick={() => dispatch({ type: "rehearse", on: false })}>Edit plan</button>
          <p className="reason">Inputs are read-only during rehearsal.</p>
        </>
      ) : (
        <button type="submit" className="btn btn-primary btn-cta" disabled={requesting || !m.baseXY}>{ICON.route}Compare routes</button>
      )}

      {requesting && (
        <div className="banner" role="status">
          <span>Requesting routes from the planning service…</span>
          <span className="indeterminate" aria-hidden="true" />
        </div>
      )}
      {state.expired && <div className="banner banner-outdated" role="alert">This plan has expired. Compare routes again.</div>}
      {freshness === "outdated" && !state.expired && (
        <div className="banner banner-outdated" role="status">Inputs changed. These results no longer match.</div>
      )}
      {freshness === "none" && <p className="reason">Compare routes to see the calculated round trip.</p>}
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
