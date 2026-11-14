import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { num, STATUS_TEXT } from "../mission/format";
import { isSample } from "../mission/geo";
import type { Mission } from "../mission/state";
import { MODE_LABEL, type Assessment, type Leg, type Mode, type XY } from "../mission/types";
import "./report.css";

const MODES: Mode[] = ["shortest", "slope_penalized"];
const xy = (p: XY | null) => (p ? `x ${num(p[0], 1)} m east, y ${num(p[1], 1)} m north` : "—");
const withUnit = (value: number | null | undefined, unit: string, digits = 0) =>
  value == null ? "—" : <>{num(value, digits)} <span className="unit">{unit}</span></>;

type Row = [label: string, cell: (a: Assessment) => ReactNode];

const legRows = (key: "outbound" | "return" | "currentToTarget" | "targetToBase", name: string): Row[] => {
  const leg = (a: Assessment): Leg | null => a[key];
  return [
    [`${name} distance`, (a) => withUnit(leg(a)?.distanceM, "m")],
    [`${name} maximum slope`, (a) => withUnit(leg(a)?.maxSlopeDeg, "°", 1)],
    [`${name} mean slope`, (a) => withUnit(leg(a)?.meanSlopeDeg, "°", 1)],
    [`${name} ascent`, (a) => withUnit(leg(a)?.ascentM, "m")],
  ];
};
const TOTALS: Row[] = [
  ["Status", (a) => STATUS_TEXT[a.status] ?? a.status],
  ["Total distance", (a) => withUnit(a.totalDistanceM, "m")],
  ["Travel time estimate", (a) => withUnit(a.travelMin, "min", 1)],
  ["Dwell", (a) => withUnit(a.dwellMin, "min", 1)],
  ["Reserve", (a) => withUnit(a.reserveMin, "min", 1)],
  ["Total time required", (a) => withUnit(a.totalRequiredMin, "min", 1)],
  ["Remaining margin", (a) => withUnit(a.marginMin, "min", 1)],
];

function Table({ caption, head, columns, rows }: { caption: string; head: ReactNode[]; columns: Assessment[]; rows: Row[] }) {
  return (
    <table className="metrics">
      <caption className="sr-only">{caption}</caption>
      <thead><tr><th scope="col">Metric</th>{head.map((h, i) => <th key={i} scope="col">{h}</th>)}</tr></thead>
      <tbody>
        {rows.map(([label, cell]) => (
          <tr key={label}><td>{label}</td>{columns.map((a, i) => <td key={i}>{cell(a)}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

export function MissionReport({ m }: { m: Mission }) {
  const { state, dispatch } = m;
  const open = state.reportOpen;
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    return () => opener?.focus();
  }, [open]);

  const { bundle, plan, planInputs: inputs, ret, stress, reach } = state;
  if (!open || !bundle || !plan || !inputs) return null;
  const close = () => dispatch({ type: "setReport", open: false });
  const sample = isSample(bundle);
  const stop = bundle.region.scienceStops.find((t) => t.id === inputs.targetId) ?? null;
  const sources = plan.sourceIds.map((id) => bundle.region.sources.find((s) => s.sourceId === id) ?? { sourceId: id, title: id, url: "" });
  const identity = (
    <p className="rp-identity">
      <span className={sample ? "tag tag-sample" : "tag"}>{sample ? "Development sample data" : "Real terrain data"}</span>{" "}
      Dataset <span className="mono">{plan.datasetVersion}</span> · Model <span className="mono">{plan.modelVersion}</span> · Plan{" "}
      <span className="mono">{plan.planId}</span>
    </p>
  );

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") return close();
    if (e.key !== "Tab") return;
    const items = dialog.current!.querySelectorAll<HTMLElement>("button, a[href]");
    const first = items[0], last = items[items.length - 1], active = document.activeElement;
    if (e.shiftKey && (active === first || active === dialog.current)) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && active === last) { e.preventDefault(); first.focus(); }
  };

  // Rendered on <body> so the print stylesheet can drop the whole app and print only this.
  return createPortal(
    <div className="report-scrim">
      <div className="report" role="dialog" aria-modal="true" aria-labelledby="rp-title" tabIndex={-1} ref={dialog} onKeyDown={onKeyDown}>
        <div className="rp-actions">
          <button type="button" className="btn btn-primary" onClick={() => window.print()}>Print or save as PDF</button>
          <button type="button" className="btn" onClick={close}>Close</button>
        </div>
        <h1 id="rp-title">Mission summary</h1>
        {identity}
        <p className="caption">An illustrative planning scenario. Routes are model results, not certified navigation or safety guidance.</p>

        <h2>1 Objective</h2>
        {stop?.scientificQuestion && <p>{stop.scientificQuestion} <span className="tag tag-hyp">Hypothetical crew scenario</span></p>}
        {stop?.description && <p>{stop.description}</p>}

        <h2>2 Destination and base</h2>
        <p><strong>Destination.</strong> {stop?.name ?? inputs.targetId} — {xy(stop?.positionXY ?? null)}</p>
        <p><strong>Base</strong> <span className="tag tag-hyp">Hypothetical</span> — {xy(m.baseXY)}</p>
        <p className="caption">Local metric frame of the region; positions are represented by {bundle.region.manifest.cellSizeM} m grid cells, not surveyed points.</p>

        <h2>3 Routes</h2>
        {/* shortcut: the 2D map image is not embedded in the report; this table is its text equivalent. Add a rendered map when the print layout needs one. */}
        <Table caption="Route metrics for both modes"
          head={MODES.map((mode) => <>{MODE_LABEL[mode]}{mode === inputs.mode && <> <span className="tag">Selected</span></>}</>)}
          columns={MODES.map((mode) => plan.options[mode])}
          rows={[...TOTALS, ...legRows("outbound", "Outbound"), ...legRows("return", "Return")]} />
        <p className="caption">Values are returned by the planning service and rounded for display. The map image is not included; this table is its text equivalent.</p>

        <h2>4 Assumptions</h2>
        <table className="metrics">
          <thead><tr><th scope="col">Input</th><th scope="col">Value</th><th scope="col">Label</th></tr></thead>
          <tbody>
            {([
              ["Route mode", MODE_LABEL[inputs.mode]],
              ["Time budget", withUnit(inputs.totalBudgetMin, "min", 1)],
              ["Slope ceiling", withUnit(inputs.maxSlopeDeg, "°", 1)],
              ["Travel speed", withUnit(inputs.speedMPerMin, "m/min", 1)],
              ["Dwell at destination", withUnit(inputs.dwellMin, "min", 1)],
              ["Reserve", withUnit(inputs.reserveMin, "min", 1)],
            ] as [string, ReactNode][]).map(([label, value]) => (
              <tr key={label}><td>{label}</td><td>{value}</td><td><span className="tag">Assumption</span></td></tr>
            ))}
            <tr><td>Base location</td><td>{xy(m.baseXY)}</td><td><span className="tag tag-hyp">Hypothetical</span></td></tr>
          </tbody>
        </table>

        {(ret.data || stress.data || reach.data) && (
          <>
            <h2>5 Scenario <span className="tag tag-hyp">Hypothetical</span></h2>
            {ret.data && (
              <>
                <p>
                  Position {xy(m.point?.xy ?? null)} on the {m.point?.leg ?? "—"} leg. Corridor blocked: {m.corridor ? "yes (preset square on the remaining path)" : "no"}.
                  Remaining time {withUnit(m.remainingMin, "min", 1)}; elapsed {withUnit(m.elapsedMin, "min", 1)} (scenario inputs).
                </p>
                <Table caption="Return options" head={["Return now", "Continue, then return"]}
                  columns={[ret.data.immediateReturn, ret.data.continueThenReturn]}
                  rows={TOTALS.map(([label, cell]): Row => [label === "Remaining margin" ? "Margin against remaining time" : label, cell])} />
              </>
            )}
            {stress.data && (
              <p>
                <strong>Closure stress test.</strong> Verdict: {stress.data.verdict}. {stress.data.survivableCount} of {stress.data.closures.length} single
                closures (radius {withUnit(stress.data.closureRadiusM, "m")}) stay within budget; worst margin {withUnit(stress.data.worstMarginMin, "min", 1)}.
              </p>
            )}
            {reach.data && (
              <p>
                <strong>Return envelope.</strong> {STATUS_TEXT[reach.data.status] ?? reach.data.status}. Allowance {withUnit(reach.data.allowanceMin, "min", 1)};
                returnable area {withUnit(reach.data.returnableAreaM2, "m²")}; farthest returnable point {withUnit(reach.data.farthestReturnableMin, "min", 1)} from base.
              </p>
            )}
          </>
        )}

        <h2>6 Sources</h2>
        <ul className="rp-sources">
          {sources.map((s) => (
            <li key={s.sourceId}>
              {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a> : s.title}
              {[s.mission, s.publicationDate ?? ("publicationDate" in s ? "date not published" : null), s.resolution]
                .filter(Boolean).map((part) => ` · ${part}`)}
              {s.limitations && <span className="rp-limit"> Limitation: {s.limitations}</span>}
            </li>
          ))}
        </ul>

        <h2>7 Limitations</h2>
        <ul>{plan.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
      </div>
    </div>,
    document.body,
  );
}
