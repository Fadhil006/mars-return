import { useEffect, useRef, useState, type CSSProperties } from "react";
import "./mission.css";
import "./rehearsal.css";
import { ElevationProfile } from "./ElevationProfile";
import { DASH, num } from "./format";
import type { Mission } from "./state";

const STEP_MS = 250; // presentation speed only; not a prediction of travel speed

/** Minutes as h:mm, display only. */
const clock = (min: number | null | undefined) => {
  if (min == null || !Number.isFinite(min)) return DASH;
  const t = Math.round(min);
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
};

export function RehearsalStrip({ m }: { m: Mission }) {
  const { state, dispatch, points, posIndex, point } = m;
  const [speed, setSpeed] = useState(1);
  const last = points.length - 1;
  const pos = useRef(posIndex);
  pos.current = posIndex;

  useEffect(() => {
    if (!state.playing) return;
    const id = setInterval(() => {
      if (pos.current >= last) dispatch({ type: "setPlaying", playing: false });
      else dispatch({ type: "setPos", index: pos.current + 1 });
    }, STEP_MS / speed);
    return () => clearInterval(id);
  }, [state.playing, speed, last, dispatch]);

  const on = state.rehearsing;
  const toggle = () => {
    if (!on) { dispatch({ type: "rehearse", on: true }); dispatch({ type: "setPlaying", playing: true }); return; }
    if (!state.playing && posIndex >= last) dispatch({ type: "setPos", index: 0 });
    dispatch({ type: "setPlaying", playing: !state.playing });
  };
  const seek = (index: number) => { dispatch({ type: "setPlaying", playing: false }); dispatch({ type: "setPos", index }); };
  const budget = state.planInputs?.totalBudgetMin;
  const speedMPerMin = state.planInputs?.speedMPerMin;
  const busy = state.ret.status === "loading" || state.reach.status === "loading";
  const totalM = points[last].alongM;
  const pct = last > 0 ? (posIndex / last) * 100 : 0;
  const stopName = (m.stop?.name ?? m.stop?.id ?? "Destination").split(" — ")[0];

  return (
    <div className="rs" onKeyDown={(e) => {
      // Space toggles playback from anywhere in the strip except controls that use Space themselves.
      if (e.key === " " && !(e.target as HTMLElement).matches("button, input:not([type=range]), select")) { e.preventDefault(); toggle(); }
    }}>
      <div className="rs-intro">
        <h2 className="rs-title">Rehearse route</h2>
        <p className="caption">Preview the planned traverse and elevation profile.</p>
        {!on && <button className="btn" onClick={() => dispatch({ type: "rehearse", on: true })}>Rehearse selected route</button>}
      </div>

      <div className="rs-main">
        <div className="rs-controls">
          <button className="rs-play" onClick={toggle} aria-label={state.playing ? "Pause" : "Play"}>{state.playing ? "❚❚" : "▶"}</button>
          <button className="rs-stop" disabled={!on} onClick={() => seek(0)} aria-label="Stop and return to start">■</button>
          <span className="rs-readout">
            <span>{point ? `${num(point.alongM / 1000, 2)} / ${num(totalM / 1000, 2)} km` : DASH}</span>
            <span>{clock(point && speedMPerMin ? point.alongM / speedMPerMin : null)} / {clock(m.assessment?.travelMin)} <abbr title="estimated travel time at the plan's speed, excluding on-site time">est.</abbr></span>
            {point && <span className="rs-leg">{point.leg === "outbound" ? "Outbound" : "Return"}</span>}
          </span>
          <input className="rs-scrub" type="range" min={0} max={last} step={1} value={posIndex} disabled={!on}
            style={{ "--pct": `${pct}%` } as CSSProperties} aria-label="Position along the route"
            aria-valuetext={point ? `${num(point.alongM)} metres of ${num(totalM)}, ${point.leg} leg` : undefined}
            onChange={(e) => seek(e.target.valueAsNumber)} />
          <label className="rs-speed caption">
            <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))} aria-label="Playback speed">
              <option value={0.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option>
            </select> presentation speed only
          </label>
        </div>
        {!on && <p className="reason">Scrubbing starts once the rehearsal starts: press Play or Rehearse selected route.</p>}
        {m.assessment && <ElevationProfile assessment={m.assessment} posIndex={posIndex} stopName={stopName} onSeek={on ? seek : undefined} />}
      </div>

      {on && <div className="rs-scenario">
        <span className="section-label">Scenario <span className="tag tag-hyp">Hypothetical</span></span>
        <label className="rs-pill"><input type="checkbox" checked={state.scenario.blocked}
          onChange={(e) => dispatch({ type: "setScenario", blocked: e.target.checked })} /> Hypothetical corridor blocked</label>
        <label className="rs-pill">Remaining time
          <input type="number" min={0} step="any" value={m.remainingMin} aria-describedby="remaining-note"
            onChange={(e) => Number.isFinite(e.target.valueAsNumber) && dispatch({ type: "setScenario", remainingMin: e.target.valueAsNumber })} />
          <span className="unit">min</span>
        </label>
        <span className="caption" id="remaining-note">
          (initial budget: {num(budget)} min; the default follows the playback position)
        </span>
        <span className="rs-actions">
          <button className="btn btn-primary" disabled={busy} onClick={m.requestReturn}>Request return options</button>
          <button className="btn" disabled={busy} onClick={m.requestReach}>Show return envelope</button>
          <button className="btn" onClick={() => dispatch({ type: "resetScenario" })}>Reset scenario</button>
        </span>
        {busy && <p className="reason" role="status">Waiting for the current request to finish.</p>}
        {state.scenario.blocked && !m.corridor && <p className="reason" role="status">Too little route remains to place a corridor here.</p>}
      </div>}
    </div>
  );
}
