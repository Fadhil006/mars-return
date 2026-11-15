import { useLayoutEffect, useState, type ReactNode } from "react";
import "./mission.css";
import { hm, num } from "./format";
import { checkNumber, type NumberLimits } from "./numberInput";
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
  // The exact text being typed, and the value before editing began. The field shows this text, never a value
  // React rebuilt from a half-typed number ("-" used to reset the field, so "-10" became 1010).
  const [draft, setDraft] = useState<{ key: NumberKey; text: string; start: number } | null>(null);
  const [rejected, setRejected] = useState<{ key: NumberKey; text: string; error: string } | null>(null);
  const stop = region.scienceStops.find((s) => s.id === inputs.targetId);
  // The field turns from formatted text into the raw number on focus; select it before the next keystroke so typing replaces the value.
  useLayoutEffect(() => { if (editing) (document.getElementById(`in-${editing}`) as HTMLInputElement | null)?.select(); }, [editing]);

  const fieldError = (key: NumberKey, limits: NumberLimits) => {
    if (draft?.key === key) { const r = checkNumber(draft.text, limits); return "error" in r ? r.error : null; }
    return rejected?.key === key ? rejected.error : null;
  };

  // Plain mono text; `show` formats the value when not being edited. Only a complete, in-range number is applied.
  const input = (key: NumberKey, label: string, limits: NumberLimits, show?: (v: number) => string) => {
    const formatted = show && editing !== key;
    const error = fieldError(key, limits);
    return (
      <input id={`in-${key}`} className="plain" aria-label={label} type="text" inputMode="decimal" autoComplete="off"
        value={formatted ? show(inputs[key]) : draft?.key === key ? draft.text : String(inputs[key])} readOnly={locked}
        aria-invalid={error ? true : undefined} aria-describedby={error ? `err-${key}` : undefined}
        onFocus={() => {
          setEditing(key);
          setDraft({ key, text: String(inputs[key]), start: inputs[key] });
          if (rejected?.key === key) setRejected(null);
        }}
        onChange={(e) => {
          const text = e.target.value;
          setDraft((d) => ({ key, text, start: d?.key === key ? d.start : inputs[key] }));
          const r = checkNumber(text, limits);
          if ("value" in r) set(key, r.value);
        }}
        onBlur={() => {
          // Leaving an invalid entry restores the value from before editing (not a half-typed prefix) and says so.
          if (draft?.key === key && error) {
            set(key, draft.start);
            setRejected({ key, text: draft.text, error });
          }
          setDraft(null);
          setEditing(null);
        }} />
    );
  };
  const errorNote = (key: NumberKey, limits: NumberLimits) => {
    const error = fieldError(key, limits);
    if (!error) return null;
    const after = draft?.key === key ? "" : ` “${rejected?.text}” was not applied; the previous value is kept.`;
    return <p id={`err-${key}`} className="reason field-error" aria-live="polite">{error}{after}</p>;
  };
  const row = (icon: ReactNode, key: NumberKey, label: string, unit: string, limits: NumberLimits, show?: (v: number) => string, extra?: ReactNode) => (
    <>
      <div className="arow">
        {icon}
        <label htmlFor={`in-${key}`}>{label}</label>
        <span className="aval">{input(key, `${label}, ${unit}`, limits, show)}{!show && <span className="unit">{unit}</span>}{extra}</span>
      </div>
      {errorNote(key, limits)}
    </>
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
        {row(ICON.rover, "speedMPerMin", "Traverse speed", "m/min", { above: 0, max: bounds.speedMPerMin[1] }, undefined,
          <span className="caption derived">({num(inputs.speedMPerMin * 0.06, 2)} km/h)</span>)}
        {row(ICON.slope, "maxSlopeDeg", "Max slope (traverse)", "°", { min: bounds.maxSlopeDeg[0], max: bounds.maxSlopeDeg[1] })}
        {row(ICON.clock, "dwellMin", "On-site science time", "minutes", { min: 0 }, dur)}
        {row(ICON.reserve, "reserveMin", "Reserve", "min", { min: 0 })}
      </section>

      <div className="budget">
        <label htmlFor="in-totalBudgetMin" className="sub-heading">Total time budget</label>
        {input("totalBudgetMin", "Total time budget, minutes", { min: 0 }, dur)}
        <span className="caption">(outbound + on-site + return + reserve)</span>
        {errorNote("totalBudgetMin", { min: 0 })}
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
      {freshness === "none" && (
        <ol className="reason getting-started" aria-label="How to use the planner">
          <li><b>Pick</b> a destination and check the assumptions.</li>
          <li><b>Compare routes</b> to see the round trip and the time it leaves spare.</li>
          <li><b>Rehearse</b> the walk, pause anywhere and ask: can we still get back?</li>
        </ol>
      )}
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
