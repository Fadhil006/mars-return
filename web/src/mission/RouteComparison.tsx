import "./mission.css";
import { diff, num, STATUS_TEXT } from "./format";
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

function ReturnOption({ m, id, title, a }: { m: Mission; id: string; title: string; a: Assessment }) {
  const hl = (field: string) => (m.state.highlight === `${id}.${field}` ? "highlight" : undefined);
  return (
    <section className="card card-hyp" aria-label={title}>
      <h4 className="option-title">{title}</h4>
      <p><Status status={a.status} /></p>
      {a.message && <p className="caption">{a.message}</p>}
      <dl className="option-metrics">
        <dt>Travel time est.</dt><dd id={`metric-${id}.travelMin`} className={hl("travelMin")}><Val v={a.travelMin} unit="min" /></dd>
        <dt>Total required</dt><dd id={`metric-${id}.totalRequiredMin`} className={hl("totalRequiredMin")}><Val v={a.totalRequiredMin} unit="min" /></dd>
        <dt>Margin against remaining time</dt><dd id={`metric-${id}.marginMin`} className={hl("marginMin")}><Val v={a.marginMin} unit="min" /></dd>
      </dl>
    </section>
  );
}

function Scenario({ m }: { m: Mission }) {
  const { ret, reach } = m.state;
  const blocked = ret.error?.message.includes("position is blocked");
  return (
    <section aria-live="polite">
      <h3 className="section-label">Return options · <span className="tag tag-hyp">Hypothetical scenario</span></h3>
      {ret.status === "idle" && <p className="reason">Pause at a position, set the scenario, then request return options.</p>}
      {ret.status === "loading" && <p role="status">Requesting return options…</p>}
      {ret.error && (
        <div className="banner banner-error" role="alert">
          {blocked ? "The current position is inside the blocked corridor. No return route can be calculated from here." : ret.error.message}
        </div>
      )}
      {ret.data && (
        <>
          <p className="caption">From the paused position with {num(m.remainingMin, 1)} min remaining.</p>
          <ReturnOption m={m} id="immediateReturn" title="Return now" a={ret.data.immediateReturn} />
          <ReturnOption m={m} id="continueThenReturn" title="Continue, then return" a={ret.data.continueThenReturn} />
        </>
      )}
      {reach.status === "loading" && <p role="status">Calculating the return envelope…</p>}
      {reach.error && <div className="banner banner-error" role="alert">{reach.error.message}</div>}
      {reach.data && (
        <section className="card card-hyp" aria-label="Return envelope">
          <h4 className="option-title">Return envelope</h4>
          <p><Status status={reach.data.status} /></p>
          <dl className="option-metrics">
            <dt>Walking allowance (remaining − reserve)</dt><dd><Val v={reach.data.allowanceMin} unit="min" /></dd>
            <dt>Area still returnable</dt><dd><Val v={reach.data.returnableAreaM2 / 1e6} unit="km²" digits={2} /></dd>
            <dt>Farthest returnable point</dt><dd><Val v={reach.data.farthestReturnableMin} unit="min from base" /></dd>
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
    <section aria-live="polite">
      <h3 className="section-label">Closure stress test · <span className="tag tag-hyp">Hypothetical</span></h3>
      <button className="btn" disabled={!m.current || stress.status === "loading"} onClick={m.requestStress}>Stress-test the way home</button>
      {!m.current && <p className="reason">Request routes to enable.</p>}
      {stress.status === "loading" && <p role="status">Testing single closures along the return…</p>}
      {stress.error && <div className="banner banner-error" role="alert">{stress.error.message}</div>}
      {d && (
        <>
          <p className={`verdict verdict-${d.verdict}`}>
            <strong>{{ robust: "Robust", fragile: "Fragile", unavailable: "Unavailable" }[d.verdict]}</strong>
            {d.verdict !== "unavailable" && <> — the return stays within budget for {d.survivableCount} of {d.closures.length} single closures
              of radius {num(d.closureRadiusM)} m. Worst margin: {d.worstMarginMin == null ? "none, a closure leaves no path" : <Val v={d.worstMarginMin} unit="min" />}.</>}
            {d.verdict === "unavailable" && " — there is no baseline round trip to test."}
          </p>
          {d.closures.length > 0 && (
            <table className="metrics closures">
              <thead><tr><th>Along return</th><th>Status</th><th>Detour</th><th>Margin</th></tr></thead>
              <tbody>{d.closures.map((c) => (
                <tr key={c.alongReturnM}>
                  <td><Val v={c.alongReturnM} unit="m" digits={0} /></td>
                  <td><Status status={c.status} /></td>
                  <td><Val v={c.detourM} unit="m" digits={0} /></td>
                  <td><Val v={c.marginMin} unit="min" /></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}

export function RouteComparison({ m }: { m: Mission }) {
  const { state, dispatch } = m, plan = state.plan;
  if (!plan || !state.planInputs) {
    return <p className="reason">{state.freshness === "requesting" ? "Requesting routes from the planning service…"
      : state.freshness === "failed" ? "No route is shown because the last request did not succeed."
      : "Request routes to compare the two route modes."}</p>;
  }
  const outdated = state.freshness !== "current";
  const s = plan.options.shortest, l = plan.options.slope_penalized, selected = plan.options[m.mode];
  const text = summary(s, l);

  return (
    <div className="routes">
      <div className={outdated ? "outdated" : undefined}>
        {outdated && <p><span className="tag tag-outdated">Outdated</span> <span className="caption">These values no longer match the inputs.</span></p>}
        <table className="metrics">
          <caption className="sr-only">Route comparison for the two modes, with the difference between them</caption>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {MODES.map((mode) => (
                <th scope="col" key={mode}>
                  <label><input type="radio" name="table-mode" checked={m.mode === mode} disabled={outdated || state.rehearsing}
                    onChange={() => dispatch({ type: "setInput", key: "mode", value: mode })} /> {MODE_LABEL[mode]}
                    {m.mode === mode && <span className="sr-only"> (selected)</span>}</label>
                </th>
              ))}
              <th scope="col">Diff</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Status</td>{MODES.map((mode) => <td key={mode} className="status-cell"><Status status={plan.options[mode].status} /></td>)}<td /></tr>
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

        {routesIdentical(plan) ? <p>Both modes return the same route for these inputs.</p> : text && <p className="prose">{text}</p>}
        {selected.status === "over_budget" && selected.marginMin != null && (
          <div className="banner banner-outdated" role="status">Exceeds the time budget by {num(-selected.marginMin, 1)} min.</div>
        )}
        {selected.status === "no_path" && (
          <div className="banner banner-error" role="status">No route was found within the slope ceiling of {num(state.planInputs.maxSlopeDeg, 1)}°.</div>
        )}
        {selected.message && <p className="caption">{selected.message}</p>}
      </div>

      {!state.rehearsing && (
        <p>
          <button className="btn" disabled={!m.current || !m.points.length} onClick={() => dispatch({ type: "rehearse", on: true })}>Rehearse selected route</button>
          {!m.current ? <span className="reason"> Request routes to enable.</span>
            : !m.points.length && <span className="reason"> The selected mode has no route to rehearse.</span>}
        </p>
      )}
      {state.rehearsing && <Scenario m={m} />}
      <Stress m={m} />
    </div>
  );
}
