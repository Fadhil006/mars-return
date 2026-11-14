import { useEffect, useRef, useState } from "react";
import "./mission.css";
import { num } from "./format";
import type { Mission } from "./state";

const STEP_MS = 250; // presentation speed only; not a prediction of travel speed

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

  if (!state.rehearsing) {
    return (
      <div className="strip-row">
        <span className="section-label">Rehearsal</span>
        <button className="btn" onClick={() => dispatch({ type: "rehearse", on: true })}>Rehearse selected route</button>
        <span className="caption">Play along the returned route, pause, and test a hypothetical change.</span>
      </div>
    );
  }

  const toggle = () => {
    if (!state.playing && posIndex >= last) dispatch({ type: "setPos", index: 0 });
    dispatch({ type: "setPlaying", playing: !state.playing });
  };
  const budget = state.planInputs?.totalBudgetMin;
  const busy = state.ret.status === "loading" || state.reach.status === "loading";

  return (
    <div className="rehearsal" onKeyDown={(e) => {
      // Space toggles playback from anywhere in the strip except controls that use Space themselves.
      if (e.key === " " && !(e.target as HTMLElement).matches("button, input:not([type=range]), select")) { e.preventDefault(); toggle(); }
    }}>
      <div className="strip-row">
        <span className="section-label">Rehearsal</span>
        <button className="btn" onClick={toggle} aria-label={state.playing ? "Pause" : "Play"}>{state.playing ? "❚❚ Pause" : "▶ Play"}</button>
        <input className="scrubber" type="range" min={0} max={last} step={1} value={posIndex} aria-label="Position along the route"
          aria-valuetext={point ? `${num(point.alongM)} metres of ${num(points[last].alongM)}, ${point.leg} leg` : undefined}
          onChange={(e) => { dispatch({ type: "setPlaying", playing: false }); dispatch({ type: "setPos", index: e.target.valueAsNumber }); }} />
        <span className="progress">
          {point && <>{num(point.alongM)} m of {num(points[last].alongM)} m · {point.leg === "outbound" ? "Outbound" : "Return"}</>}
        </span>
        <label className="caption">Playback{" "}
          <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))} aria-label="Playback speed">
            <option value={0.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option>
          </select>{" "}· presentation speed only
        </label>
      </div>

      <div className="strip-row">
        <span className="section-label">Scenario <span className="tag tag-hyp">Hypothetical</span></span>
        <label><input type="checkbox" checked={state.scenario.blocked}
          onChange={(e) => dispatch({ type: "setScenario", blocked: e.target.checked })} /> Hypothetical corridor blocked</label>
        <label className="remaining">Remaining time{" "}
          <input type="number" min={0} step="any" value={m.remainingMin} aria-describedby="remaining-note"
            onChange={(e) => Number.isFinite(e.target.valueAsNumber) && dispatch({ type: "setScenario", remainingMin: e.target.valueAsNumber })} />
          {" "}<span className="unit">min</span>
        </label>
        <span className="caption" id="remaining-note">
          (initial budget: {num(budget)} min; the default follows the playback position)
        </span>
        <button className="btn btn-primary" disabled={busy} onClick={m.requestReturn}>Request return options</button>
        <button className="btn" disabled={busy} onClick={m.requestReach}>Show return envelope</button>
        <button className="btn" onClick={() => dispatch({ type: "resetScenario" })}>Reset scenario</button>
      </div>
      {state.scenario.blocked && !m.corridor && <p className="reason" role="status">Too little route remains to place a corridor here.</p>}
    </div>
  );
}
