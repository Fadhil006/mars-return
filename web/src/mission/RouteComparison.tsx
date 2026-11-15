import { useEffect, useRef, useState } from "react";
import { callFeedback, DECIDE_SECONDS } from "./decide";
import "./mission.css";
import "./routes.css";
import { diff, doseMSv, hm, num, RAD_MSV_PER_DAY, STATUS_TEXT, turnaround } from "./format";
import { routesIdentical } from "./geo";
import type { Mission } from "./state";
import { MODE_LABEL, type Assessment, type Mode } from "./types";

const MODES = Object.keys(MODE_LABEL) as Mode[];
type Row = [id: string, label: string, unit: string, digits: number, get: (a: Assessment) => number | null | undefined];
const ROWS: Row[] = [
  ["totalDistanceM", "Distance", "m", 0, (a) => a.totalDistanceM],
  ["travelMin", "Travel time est.", "min", 1, (a) => a.travelMin],
  ["outbound.maxSlopeDeg", "Outbound max slope", "°", 1, (a) => a.outbound?.maxSlopeDeg],
  ["return.maxSlopeDeg", "Return max slope", "°", 1, (a) => a.return?.maxSlopeDeg],
  ["outbound.meanSlopeDeg", "Outbound mean slope", "°", 1, (a) => a.outbound?.meanSlopeDeg],
  ["return.meanSlopeDeg", "Return mean slope", "°", 1, (a) => a.return?.meanSlopeDeg],
  ["outbound.ascentM", "Outbound ascent", "m", 1, (a) => a.outbound?.ascentM],
  ["return.ascentM", "Return ascent", "m", 1, (a) => a.return?.ascentM],
  ["dwellMin", "Dwell", "min", 0, (a) => a.dwellMin],
  ["reserveMin", "Reserve", "min", 0, (a) => a.reserveMin],
  ["totalRequiredMin", "Total required", "min", 1, (a) => a.totalRequiredMin],
  ["marginMin", "Remaining margin", "min", 1, (a) => a.marginMin],
];

const Status = ({ status }: { status: string }) => <span className={`status status-${status}`}>{STATUS_TEXT[status] ?? status}</span>;
const Val = ({ v, unit, digits = 1 }: { v: number | null | undefined; unit: string; digits?: number }) =>
  <>{num(v, digits)}{v != null && <>&thinsp;<span className="unit">{unit}</span></>}</>;
const Hm = ({ v }: { v: number | null | undefined }) => <span className="rc-num">{hm(v)}</span>;
const km = (m: number | null | undefined) => (m == null ? "—" : m >= 1000 ? `${num(m / 1000, 2)} km` : `${num(m)} m`);
// Display only: the larger of the two returned leg maxima.
const maxSlope = (a: Assessment) => {
  const v = [a.outbound?.maxSlopeDeg, a.return?.maxSlopeDeg].filter((x): x is number => x != null);
  return v.length ? `${num(Math.max(...v))}°` : "—";
};

/** One sentence from returned differences only; a property is named only for the mode it actually improves. */
function summary(s: Assessment, l: Assessment): string | null {
  const better = (a: Assessment, b: Assessment) => [
    a.totalDistanceM != null && b.totalDistanceM != null && a.totalDistanceM < b.totalDistanceM
      && `${num(b.totalDistanceM - a.totalDistanceM)} m shorter`,
    a.marginMin != null && b.marginMin != null && a.marginMin > b.marginMin
      && `${num(a.marginMin - b.marginMin, 1)} min more margin`,
    ...(["outbound", "return"] as const).map((leg) => {
      const x = a[leg]?.maxSlopeDeg, y = b[leg]?.maxSlopeDeg;
      return x != null && y != null && x < y && `${num(y - x, 1)}° lower maximum slope ${leg === "outbound" ? "outbound" : "on the return"}`;
    }),
  ].filter(Boolean).join(", ");
  const parts = [[MODE_LABEL.shortest, better(s, l)], [MODE_LABEL.slope_penalized, better(l, s)]]
    .filter(([, text]) => text).map(([name, text]) => `${name}: ${text}`);
  return parts.length ? `${parts.join(". ")}.` : null;
}

/**
 * The answer first: the selected route's remaining margin, and how the time budget divides. Every segment is a
 * returned value (travel, dwell, reserve, margin) except the budget, which is the plan's own input.
 */
function Headline({ a, mode, budget, outdated }: { a: Assessment; mode: Mode; budget: number; outdated: boolean }) {
  const parts = [
    { key: "travel", label: "Travel", v: a.travelMin },
    { key: "dwell", label: "On site", v: a.dwellMin },
    { key: "reserve", label: "Reserve", v: a.reserveMin },
    { key: "margin", label: "Margin", v: a.marginMin != null && a.marginMin > 0 ? a.marginMin : 0 },
  ];
  const known = parts.every((p) => p.v != null) && a.totalRequiredMin != null;
  const scale = Math.max(budget, a.totalRequiredMin ?? 0) || 1;
  const over = a.marginMin != null && a.marginMin < 0;
  const outside = a.travelMin != null && a.dwellMin != null ? a.travelMin + a.dwellMin : null;
  return (
    <section className={`rc-hero${outdated ? " outdated" : ""}${over ? " is-over" : ""}`} aria-label={`Selected route: ${MODE_LABEL[mode]}`}>
      <div className="rc-hero-top">
        <span className="section-label">Remaining margin</span>
        <Status status={a.status} />
      </div>
      <p className="rc-hero-num" id={`metric-${mode}.marginMin-hero`}>{hm(a.marginMin)}</p>
      <p className="caption">{MODE_LABEL[mode]} · {hm(a.totalRequiredMin)} required of a {hm(budget)} budget (assumption)</p>
      {known && (
        <div className="rc-budget" role="img"
          aria-label={`Time budget: ${parts.map((p) => `${p.label} ${hm(p.v)}`).join(", ")}${over ? `; exceeds the budget by ${hm(-a.marginMin!)}` : ""}.`}>
          <div className="rc-budget-bar">
            {parts.map((p) => p.v! > 0 && <span key={p.key} className={`seg seg-${p.key}`} style={{ width: `${(p.v! / scale) * 100}%` }} />)}
            {over && <span className="rc-budget-line" style={{ left: `${(budget / scale) * 100}%` }} title="Budget" />}
          </div>
          <ul className="rc-budget-key" aria-hidden="true">
            {parts.map((p) => <li key={p.key}><span className={`dot seg-${p.key}`} />{p.label} <b>{hm(p.v)}</b></li>)}
          </ul>
        </div>
      )}
      <ContactVerdict a={a} id={mode} />
      {outside != null && (
        <div className="rc-dose" title="Curiosity RAD, Gale Crater, Aug 2012 to Jun 2013 (Hassler et al. 2014, Science). Galactic cosmic rays only; a solar particle event would add more.">
          <div className="rc-hero-top">
            <span className="section-label">Radiation dose est.</span>
            <span className="tag">NASA MSL RAD</span>
          </div>
          <p className="rc-dose-num">≈ {num(doseMSv(outside), 2)} <span>mSv</span></p>
          <p className="caption">
            {hm(outside)} outside (travel + on site) at the {RAD_MSV_PER_DAY} mSv/day Curiosity's RAD measured on the surface at Gale Crater.
            Jezero sits about 2 km higher, so its dose is likely a little higher; no solar storm included.
          </p>
        </div>
      )}
    </section>
  );
}

/** Second verdict from the server: the longest continuous time out of sight of base against the hypothetical rule. */
export function ContactVerdict({ a, id }: { a: Assessment; id: string }) {
  if (a.contactStatus == null) return null;
  const over = a.contactStatus === "exceeds_rule";
  return (
    <div className={`rc-contact${over ? " is-over" : ""}`}>
      <div className="rc-hero-top">
        <span className="section-label">Out of sight of base</span>
        <span className={`status ${over ? "status-contact" : "status-ok"}`}>{over ? "Exceeds contact rule" : "Within contact rule"}</span>
      </div>
      <p className="rc-dose-num" id={`metric-${id}.longestOutOfContactMin`}>{hm(a.longestOutOfContactMin)} <span>longest stretch</span></p>
      <p className="caption">
        {hm(a.outOfContactMin)} in total out of line of sight of the base mast; rule: no more than {hm(a.maxOutOfContactMin)} at a time
        (hypothetical). Line of sight on 20 m terrain; no relays or radio effects modelled.
      </p>
    </div>
  );
}

function ReturnOption({ m, id, title, a }: { m: Mission; id: string; title: string; a: Assessment }) {
  const hl = (field: string) => (m.state.highlight === `${id}.${field}` ? "highlight" : undefined);
  return (
    <section className="card card-hyp" aria-label={title}>
      <h4 className="option-title">{title}</h4>
      <p><Status status={a.status} /></p>
      {a.message && <p className="caption">{a.message}</p>}
      <dl className="option-metrics">
        <dt>Travel time est.</dt><dd id={`metric-${id}.travelMin`} className={hl("travelMin")}><Hm v={a.travelMin} /></dd>
        <dt>Total required</dt><dd id={`metric-${id}.totalRequiredMin`} className={hl("totalRequiredMin")}><Hm v={a.totalRequiredMin} /></dd>
        <dt>Margin against remaining time</dt><dd id={`metric-${id}.marginMin`} className={hl("marginMin")}><Hm v={a.marginMin} /></dd>
        {a.contactStatus != null && <>
          <dt>Longest out of sight of base</dt>
          <dd id={`metric-${id}.longestOutOfContactMin`} className={hl("longestOutOfContactMin")}>
            <Hm v={a.longestOutOfContactMin} />{a.contactStatus === "exceeds_rule" && <> <span className="status status-contact">Exceeds rule</span></>}
          </dd>
        </>}
      </dl>
    </section>
  );
}

/** The user commits to a call before the planner's options are shown; silence after the countdown is recorded too. */
function DecideFirst({ m }: { m: Mission }) {
  const [left, setLeft] = useState(DECIDE_SECONDS);
  const decide = (call: "return" | "continue" | "none" | "skip") => m.dispatch({ type: "makeCall", call });
  useEffect(() => {
    if (left <= 0) { decide("none"); return; }
    const timer = window.setTimeout(() => setLeft(left - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [left]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="card decide" role="group" aria-label="Make the call before seeing the planner's options">
      <p className="decide-q"><strong>Your call.</strong> The crew is paused here with {hm(m.remainingMin)} remaining. Turn back, or carry on to the site?</p>
      <div className="decide-buttons">
        <button className="btn btn-primary" onClick={() => decide("return")}>Return now</button>
        <button className="btn btn-primary" onClick={() => decide("continue")}>Continue, then return</button>
      </div>
      <div className="decide-timer" aria-hidden="true"><span style={{ width: `${(left / DECIDE_SECONDS) * 100}%` }} /></div>
      <p className="caption" role="timer" aria-live="off">{left} s left · the planner's numbers appear after you decide.{" "}
        <button className="link-btn" onClick={() => decide("skip")}>Skip and show results</button></p>
    </div>
  );
}

function Scenario({ m }: { m: Mission }) {
  const { ret, reach } = m.state;
  const blocked = ret.error?.message.startsWith("current position is blocked");
  const ref = useRef<HTMLElement>(null);
  // New return options land below the route comparison; bring them into view so they are not missed on short screens.
  useEffect(() => {
    if (ret.status !== "ok" && ret.status !== "error") return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // "start": the section can be taller than the panel, and "nearest" would then leave the second option below the fold.
    ref.current?.scrollIntoView({ block: "start", behavior: reduce ? "auto" : "smooth" });
  }, [ret.status, ret.requestId]);
  return (
    <section className="rc-section" aria-live="polite" ref={ref}>
      <h3 className="rc-h3">Return options <span className="tag tag-hyp">Hypothetical scenario</span></h3>
      {ret.status === "idle" && <p className="reason">Pause at a position, set the scenario, then request return options.</p>}
      {ret.status !== "idle" && !ret.error && m.state.call == null && <DecideFirst key={ret.requestId} m={m} />}
      {ret.status === "loading" && m.state.call != null && <p role="status">Requesting return options…</p>}
      {ret.error && (
        <div className="banner banner-error" role="alert">
          {blocked ? "The current position is inside the blocked corridor. No return route can be calculated from here." : ret.error.message}
        </div>
      )}
      {ret.data && m.state.call != null && (
        <>
          {(() => {
            const line = callFeedback(m.state.call!, ret.data);
            return line && <p className="decide-feedback" role="status"><strong>{line}</strong></p>;
          })()}
          <p className="caption">From the paused position with {hm(m.remainingMin)} remaining.</p>
          <ReturnOption m={m} id="immediateReturn" title="Return now" a={ret.data.immediateReturn} />
          <ReturnOption m={m} id="continueThenReturn" title="Continue, then return" a={ret.data.continueThenReturn} />
          {(() => {
            const call = turnaround(ret.data.immediateReturn, ret.data.continueThenReturn);
            return call && <p className="verdict"><strong>{call}</strong></p>;
          })()}
        </>
      )}
      {reach.status === "loading" && <p role="status">Calculating the return envelope…</p>}
      {reach.error && <div className="banner banner-error" role="alert">{reach.error.message}</div>}
      {reach.data && (
        <section className="card card-hyp" aria-label="Return envelope">
          <h4 className="option-title">Return envelope</h4>
          <p><Status status={reach.data.status} /></p>
          <dl className="option-metrics">
            <dt>Walking allowance (remaining − reserve)</dt><dd><Hm v={reach.data.allowanceMin} /></dd>
            <dt>Area still returnable</dt><dd className="rc-num"><Val v={reach.data.returnableAreaM2 / 1e6} unit="km²" digits={2} /></dd>
            <dt>Farthest returnable point</dt><dd><Hm v={reach.data.farthestReturnableMin} /> <span className="unit">from base</span></dd>
          </dl>
          <p className="caption">Shown on the map as the “Return envelope” layer.</p>
        </section>
      )}
    </section>
  );
}

function Stress({ m }: { m: Mission }) {
  const { stress } = m.state, d = stress.data;
  return (
    <section className="rc-section" aria-live="polite">
      <h3 className="rc-h3">Closure stress test <span className="tag tag-hyp">Hypothetical</span></h3>
      <button className="btn" disabled={!m.current || stress.status === "loading"} onClick={m.requestStress}>Stress-test the way home</button>
      {!m.current && <p className="reason">Request routes to enable.</p>}
      {stress.status === "loading" && <p role="status">Testing single closures along the return…</p>}
      {stress.error && <div className="banner banner-error" role="alert">{stress.error.message}</div>}
      {d && (
        <div className="card card-hyp">
          <p className={`verdict verdict-${d.verdict}`}>
            <strong>{{ robust: "Robust", fragile: "Fragile", unavailable: "Unavailable" }[d.verdict]}</strong>
            {d.verdict !== "unavailable" && <> — the return stays within budget for {d.survivableCount} of {d.closures.length} single closures
              of radius {num(d.closureRadiusM)} m. Worst margin: {d.worstMarginMin == null ? "none, a closure leaves no path" : <Hm v={d.worstMarginMin} />}.</>}
            {d.verdict === "unavailable" && (d.baseline.totalDistanceM == null
              ? " — there is no baseline round trip to test."
              : ` — the way home is too short to place a ${num(d.closureRadiusM)} m closure clear of the base and the site.`)}
          </p>
          {d.closures.length > 0 && (
            <table className="metrics closures">
              <thead><tr><th>Along return</th><th>Status</th><th>Detour</th><th>Margin</th></tr></thead>
              <tbody>{d.closures.map((c) => (
                <tr key={c.alongReturnM}>
                  <td className="rc-num">{km(c.alongReturnM)}</td>
                  <td><Status status={c.status} /></td>
                  <td className="rc-num">{km(c.detourM)}</td>
                  <td><Hm v={c.marginMin} /></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}

/** Why this stop matters, from the stop's own record only; shown before any route is requested. */
function WhyVisit({ m }: { m: Mission }) {
  const stop = m.stop, sources = m.state.bundle?.region.sources ?? [];
  if (!stop) return null;
  const titles = stop.sourceIds.map((id) => sources.find((s) => s.sourceId === id)?.title ?? id);
  return (
    <section className="rc-section rc-why">
      <h3 className="rc-h2">Why visit this stop?</h3>
      {stop.description && <p>{stop.description}</p>}
      {stop.scientificQuestion && (
        <>
          <p className="rc-h3">Excursion question <span className="tag tag-hyp">Hypothetical crew scenario</span></p>
          <p>{stop.scientificQuestion}</p>
        </>
      )}
      {!!titles.length && (
        <button type="button" className="src-line" onClick={() => m.dispatch({ type: "setTab", tab: "evidence" })}>
          Sources: {titles.join("; ")}.
        </button>
      )}
    </section>
  );
}

export function RouteComparison({ m }: { m: Mission }) {
  const { state, dispatch } = m, plan = state.plan;
  // A cited metric may sit below the fold or inside the collapsed full table; open it and bring it into view.
  useEffect(() => {
    if (!state.highlight) return;
    const el = document.getElementById(`metric-${state.highlight}`);
    const details = el?.closest("details");
    if (details) details.open = true;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" });
  }, [state.highlight]);

  const shown = plan && state.planInputs ? plan : null;
  const outdated = state.freshness !== "current";

  return (
    <div className="routes">
      <h2 className="rc-h2 rc-title">Route comparison <span className="rc-sub">(model results)</span></h2>
      {shown && outdated && <p><span className="tag tag-outdated">Outdated</span> <span className="caption">These values no longer match the inputs.</span></p>}

      {shown && state.planInputs && <Headline a={shown.options[m.mode]} mode={m.mode} budget={state.planInputs.totalBudgetMin} outdated={outdated} />}

      {/* The only route-mode selector; both modes are in one plan, so switching is not a new calculation. */}
      <fieldset className={`rc-modes${shown && outdated ? " outdated" : ""}`} disabled={state.rehearsing}>
        <legend className="sr-only">Route mode</legend>
        {MODES.map((mode) => {
          const a = shown?.options[mode];
          return (
            <div className={`rc-row${state.inputs.mode === mode ? " is-selected" : ""}`} key={mode}>
              <label className="rc-name">
                <input type="radio" name="table-mode" checked={state.inputs.mode === mode}
                  onChange={() => dispatch({ type: "setInput", key: "mode", value: mode })} />
                <span>{MODE_LABEL[mode]}</span>
              </label>
              {a && (
                <dl className="rc-figs">
                  {a.status !== "ok" && <div className="rc-status"><dt className="sr-only">Status</dt><dd><Status status={a.status} /></dd></div>}
                  <div><dt>Distance</dt><dd>{km(a.totalDistanceM)}</dd></div>
                  <div><dt>Total time</dt><dd>{hm(a.totalRequiredMin)}</dd></div>
                  <div><dt>Max slope</dt><dd>{maxSlope(a)}</dd></div>
                  <div><dt>Margin</dt><dd>{hm(a.marginMin)}</dd></div>
                </dl>
              )}
            </div>
          );
        })}
      </fieldset>

      {shown ? <Compare m={m} plan={shown} outdated={outdated} /> : (
        <p className="reason rc-prompt">{state.freshness === "requesting" ? "Requesting routes from the planning service…"
          : state.freshness === "failed" ? "No route is shown because the last request did not succeed."
          : "Compare routes to see options."}</p>
      )}

      <WhyVisit m={m} />

      {shown && !state.rehearsing && (
        <p>
          <button className="btn" disabled={!m.current || !m.points.length} onClick={() => dispatch({ type: "rehearse", on: true })}>Rehearse selected route</button>
          {!m.current ? <span className="reason"> Request routes to enable.</span>
            : !m.points.length && <span className="reason"> The selected mode has no route to rehearse.</span>}
        </p>
      )}
      {state.rehearsing && <Scenario m={m} />}
      {shown && <Stress m={m} />}
    </div>
  );
}

function Compare({ m, plan, outdated }: { m: Mission; plan: NonNullable<Mission["state"]["plan"]>; outdated: boolean }) {
  const { state } = m, s = plan.options.shortest, l = plan.options.slope_penalized, selected = plan.options[m.mode];
  const text = summary(s, l);
  return (
    <div className={outdated ? "outdated" : undefined}>
      {routesIdentical(plan) ? <p className="rc-summary">Both modes return the same route for these inputs.</p> : text && <p className="rc-summary">{text}</p>}
      {selected.status === "over_budget" && selected.marginMin != null && (
        <div className="banner banner-outdated" role="status">Exceeds the time budget by {hm(-selected.marginMin)}.</div>
      )}
      {selected.status === "no_path" && (
        <div className="banner banner-error" role="status">No route was found within the slope ceiling of {num(state.planInputs?.maxSlopeDeg, 1)}°.</div>
      )}
      {selected.message && <p className="caption">{selected.message}</p>}

      <details className="rc-full">
        <summary>Full comparison</summary>
        <table className="metrics">
          <caption className="sr-only">Route comparison for the two modes, with the difference between them</caption>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {MODES.map((mode) => <th scope="col" key={mode}>{MODE_LABEL[mode]}{m.mode === mode && <span className="sr-only"> (selected)</span>}</th>)}
              <th scope="col">Diff</th>
            </tr>
          </thead>
          <tbody>
            <tr className={MODES.some((mode) => state.highlight === `${mode}.status`) ? "highlight" : undefined}>
              <td>Status</td>{MODES.map((mode) => <td key={mode} id={`metric-${mode}.status`} className="status-cell"><Status status={plan.options[mode].status} /></td>)}<td />
            </tr>
            {ROWS.map(([id, label, unit, digits, get]) => (
              <tr key={id} className={MODES.some((mode) => state.highlight === `${mode}.${id}`) ? "highlight" : undefined}>
                <td>{label}</td>
                {MODES.map((mode) => <td key={mode} id={`metric-${mode}.${id}`}><Val v={get(plan.options[mode])} unit={unit} digits={digits} /></td>)}
                <td className="delta">{diff(get(s), get(l), digits)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="caption">Diff is {MODE_LABEL.slope_penalized} minus {MODE_LABEL.shortest}, from the returned values. Values are rounded for display only.</p>
      </details>
    </div>
  );
}
