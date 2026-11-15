import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import "./app.css";
import { MissionAssistant } from "./assistant/MissionAssistant";
import { EvidencePanel } from "./evidence/EvidencePanel";
import { MissionMap } from "./map/MissionMap";
import { isSample } from "./mission/geo";
import { MissionControls } from "./mission/MissionControls";
import { RehearsalStrip } from "./mission/RehearsalStrip";
import { RouteComparison } from "./mission/RouteComparison";
import { useMission, type Freshness, type LayerKey, type Mission, type Tab } from "./mission/state";
import { MissionReport } from "./report/MissionReport";
import { TerrainView, webglAvailable } from "./terrain/TerrainView";

const FRESH: Record<Freshness, [string, string]> = {
  none: ["No result yet", ""], requesting: ["Updating", "status-updating"], current: ["Current", "status-current"],
  outdated: ["Outdated", "status-outdated"], failed: ["Failed", "status-error"],
};
const TABS: Tab[] = ["routes", "evidence", "assistant"];
const TAB_LABEL: Record<Tab, string> = { routes: "Routes", evidence: "Evidence", assistant: "Assistant" };
const NO_3D = "3D terrain is not available in this browser. The 2D map has the same route and controls.";
const webgl = webglAvailable(); // checked once; creating contexts repeatedly exhausts the browser's limit
const wide = window.matchMedia("(min-width: 900px)").matches; // small screens start with versions collapsed (design 12)
const TODAY = new Date();

const icon = (d: ReactNode) => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>
);
const LAYERS_ICON = icon(<><path d="M12 4 3 9l9 5 9-5z" /><path d="m3 13 9 5 9-5" /></>);
const FULL_ICON = icon(<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" />);
const EXIT_ICON = icon(<path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5" />);

function Layers({ m }: { m: Mission }) {
  const { state, dispatch } = m, b = state.bundle!;
  const rows: [LayerKey, string, string | null][] = [
    ["imagery", "Imagery", b.imageryUrl ? null : "Imagery could not be loaded."],
    ["slope", "Slope, derived from elevation", b.slope ? null : "Slope data could not be loaded."],
    ["stops", "Science stops", null],
    ["labels", "Site labels", state.layers.stops ? null : "Turn on science stops to label them."],
    ["traverse", "Perseverance traverse", b.traverse ? null : "This region has no rover traverse."],
    ["envelope", "Return envelope", state.reach.data ? null : "Request the return envelope during rehearsal."],
    ["contact", "Out of sight of base", state.plan?.contact ? null : "Compare routes to calculate line of sight."],
  ];
  return (
    <details className="layers">
      <summary className="icon-btn" aria-label="Layers" title="Layers">{LAYERS_ICON}</summary>
      <div className="layers-menu">
        {rows.map(([key, label, reason]) => (
          <div key={key}>
            <label><input type="checkbox" checked={state.layers[key] && !reason} disabled={!!reason}
              onChange={() => dispatch({ type: "toggleLayer", key })} /> {label}</label>
            {reason && <p className="reason">{reason}</p>}
          </div>
        ))}
      </div>
    </details>
  );
}

export function App() {
  const m = useMission();
  const { state, dispatch } = m;
  const [pane, setPane] = useState<"mission" | "map" | "results">("map"); // narrow screens
  const [drawer, setDrawer] = useState(false); // medium screens
  const viewRef = useRef<HTMLElement>(null);
  const barRef = useRef<HTMLElement>(null);
  // The plan drawer on medium screens starts under the header, whose height depends on wrapping.
  useEffect(() => {
    const bar = barRef.current;
    if (!bar) return;
    const observer = new ResizeObserver(() => document.documentElement.style.setProperty("--bar-h", `${bar.offsetHeight}px`));
    observer.observe(bar);
    return () => observer.disconnect();
  }, [state.bundle]);
  const [full, setFull] = useState(false);
  useEffect(() => {
    const on = () => setFull(!!viewRef.current && document.fullscreenElement === viewRef.current);
    document.addEventListener("fullscreenchange", on);
    return () => document.removeEventListener("fullscreenchange", on);
  }, []);

  if (!state.bundle) {
    return (
      <main className="app-gate">
        {state.regionStatus === "error" ? (
          <div role="alert">
            <h1 className="panel-heading">The planning data for this region could not be loaded.</h1>
            <p>{state.regionError?.message}</p>
            <button className="btn btn-primary" onClick={m.loadRegion}>Retry</button>
          </div>
        ) : (
          <div className="loading" role="status" aria-live="polite">
            <svg className="loading-mark" width="56" height="56" viewBox="0 0 26 26" fill="none" aria-hidden="true">
              <circle cx="13" cy="13" r="11.5" stroke="currentColor" strokeOpacity="0.25" />
              <path className="loading-arc" d="M13 1.5a11.5 11.5 0 0 1 11.5 11.5" stroke="#3dd6e8" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <h1 className="loading-title">Loading the region</h1>
            {/* What is actually being fetched, in order; no invented progress percentage. */}
            <ul className="loading-list">
              <li>Region manifest and Perseverance sampling sites</li>
              <li>MRO CTX elevation, 20 m cells</li>
              <li>CTX image, 5 m pixels</li>
              <li>Slope and missing-data mask</li>
            </ul>
          </div>
        )}
      </main>
    );
  }

  const b = state.bundle, region = b.region;
  const [freshText, freshClass] = FRESH[state.freshness];
  const no3d = !webgl || !b.elevation;
  const noPath = m.assessment?.status === "no_path"; // design 10: no_path blocks Rehearse and Report
  const view = no3d ? "2d" : state.view;
  const canRehearse = m.current && m.points.length > 0, canReport = m.current && !noPath;
  const rehearseReason = "Compare routes to enable rehearsal.";
  const reportReason = !m.current ? "Compare routes to enable. The report never exports an outdated result."
    : "The selected mode found no route, so there is nothing to report.";
  const phase = state.reportOpen ? "report" : state.rehearsing ? "rehearse" : "plan";
  const toPlan = () => {
    if (state.rehearsing) dispatch({ type: "rehearse", on: false });
    setPane("mission");
    if (window.matchMedia("(min-width: 900px) and (max-width: 1199px)").matches) setDrawer(true);
    requestAnimationFrame(() => document.getElementById("in-target")?.focus());
  };
  const toggleFull = () => { (full ? document.exitFullscreen() : viewRef.current?.requestFullscreen())?.catch(() => {}); };
  const onTabKey = (e: KeyboardEvent) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const tab = TABS[(TABS.indexOf(state.tab) + step + TABS.length) % TABS.length];
    dispatch({ type: "setTab", tab });
    document.getElementById(`tab-${tab}`)?.focus();
  };

  return (
    <div className={`app pane-${pane}${drawer ? " drawer-open" : ""}`}>
      <header className="bar" ref={barRef}>
        <div className="bar-row">
          <button className="btn drawer-toggle" aria-expanded={drawer} onClick={() => setDrawer(!drawer)}>Plan panel</button>
          <span className="brand">
            {/* Brand mark: a route loop out from a base and back. Decorative, hidden from assistive tech. */}
            <svg className="brand-mark" width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
              <circle cx="13" cy="13" r="11.5" stroke="currentColor" strokeOpacity="0.35" />
              <path d="M7 17c2-6 6-9 12-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              <path d="M19 8c-1 5-5 8-12 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 2.5" />
              <rect x="5.5" y="15.5" width="3" height="3" fill="currentColor" /><circle cx="19" cy="8" r="2" fill="#3dd6e8" />
            </svg>
            <h1 className="product"><b>Mars</b> <span className="slash">/</span> Excursion planner</h1>
          </span>
          {isSample(b) ? <span className="tag tag-sample">Development sample data</span>
            : <span className="tag tag-data">Real CTX terrain · Jezero Crater</span>}
          <span className="bar-end">
            <time className="today" dateTime={TODAY.toISOString().slice(0, 10)}>
              {TODAY.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}
            </time>
            <span className={`status ${freshClass} fresh`} aria-live="polite">{freshText}</span>
          </span>
        </div>
        <div className="bar-row bar-row2">
          <h2 className="mc-title">Mission Control</h2>
          <nav className="phase" aria-label="Mission phase">
            <button aria-current={phase === "plan" ? "step" : undefined} onClick={toPlan}>Plan</button>
            <button aria-current={phase === "rehearse" ? "step" : undefined} disabled={!canRehearse}
              title={canRehearse ? undefined : rehearseReason} aria-description={canRehearse ? undefined : rehearseReason}
              onClick={() => { dispatch({ type: "rehearse", on: true }); setPane("map"); }}>Rehearse</button>
            <button aria-current={phase === "report" ? "step" : undefined} disabled={!canReport}
              title={canReport ? undefined : reportReason} aria-description={canReport ? undefined : reportReason}
              onClick={() => dispatch({ type: "setReport", open: true })}>Report</button>
          </nav>
          <span className="caption assume-note">Time estimates depend on selected assumptions.</span>
          <details className="versions" open={wide}>
            <summary>Versions</summary>
            <span className="mono">Dataset {region.datasetVersion}</span>
            <span className="mono" title={state.plan?.planId}>Plan {state.plan ? state.plan.planId.slice(0, 8) : "—"}</span>
            <span className="mono">Model {state.plan?.modelVersion ?? "—"}</span>
          </details>
        </div>
      </header>

      <nav className="panes" aria-label="Sections">
        {(["mission", "map", "results"] as const).map((p) => (
          <button key={p} className="btn" aria-pressed={pane === p} onClick={() => setPane(p)}>
            {p[0].toUpperCase() + p.slice(1)}
          </button>
        ))}
      </nav>

      <aside className="col left" aria-label="Excursion plan">
        <MissionControls m={m} />
      </aside>

      <main className="view" aria-label="Viewing area" ref={viewRef}>
        <div className="toolbar">
          <div className="tool-row">
            <div className="segments" role="group" aria-label="View">
              <button aria-pressed={view === "2d"} onClick={() => dispatch({ type: "setView", view: "2d" })}>2D<span className="sr-only"> map</span></button>
              <button aria-pressed={view === "3d"} disabled={no3d} aria-describedby={no3d ? "no3d" : undefined}
                onClick={() => dispatch({ type: "setView", view: "3d" })}>3D<span className="sr-only"> terrain</span></button>
            </div>
            <div className="tool-group">
              <Layers m={m} />
              <button className="icon-btn" aria-label={full ? "Exit full screen" : "Full screen"} title={full ? "Exit full screen" : "Full screen"}
                onClick={toggleFull}>{full ? EXIT_ICON : FULL_ICON}</button>
            </div>
          </div>
          {no3d && <p className="reason" id="no3d">{webgl ? "3D terrain needs the elevation layer, which could not be loaded." : NO_3D}</p>}
        </div>
        <div className="canvas">{view === "3d" ? <TerrainView m={m} /> : <MissionMap m={m} />}</div>
      </main>

      <aside className="col right" aria-label="Results">
        <div role="tablist" aria-label="Results" className="tabs" onKeyDown={onTabKey}>
          {TABS.map((t) => (
            <button key={t} id={`tab-${t}`} role="tab" aria-selected={state.tab === t} aria-controls="tabpanel"
              tabIndex={state.tab === t ? 0 : -1} onClick={() => dispatch({ type: "setTab", tab: t })}>{TAB_LABEL[t]}</button>
          ))}
        </div>
        <div id="tabpanel" role="tabpanel" aria-labelledby={`tab-${state.tab}`} className="tabpanel">
          {state.tab === "routes" ? <RouteComparison m={m} /> : state.tab === "evidence" ? <EvidencePanel m={m} /> : <MissionAssistant m={m} />}
        </div>
        <div className="report-open">
          <button className="btn" disabled={!canReport} onClick={() => dispatch({ type: "setReport", open: true })}>Open mission report</button>
          {!canReport && <p className="reason">{reportReason}</p>}
        </div>
      </aside>

      {canRehearse && <footer className="strip"><RehearsalStrip m={m} /></footer>}
      <MissionReport m={m} />
    </div>
  );
}
