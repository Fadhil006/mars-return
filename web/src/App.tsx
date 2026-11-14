import { useState, type KeyboardEvent } from "react";
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

function Layers({ m }: { m: Mission }) {
  const { state, dispatch } = m, b = state.bundle!;
  const rows: [LayerKey, string, string | null][] = [
    ["imagery", "Imagery", b.imageryUrl ? null : "Imagery could not be loaded."],
    ["slope", "Slope, derived from elevation", b.slope ? null : "Slope data could not be loaded."],
    ["stops", "Science stops", null],
    ["traverse", "Perseverance traverse", b.traverse ? null : "This region has no rover traverse."],
    ["envelope", "Return envelope", state.reach.data ? null : "Request the return envelope during rehearsal."],
  ];
  return (
    <details className="layers">
      <summary className="btn">Layers</summary>
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

  if (!state.bundle) {
    return (
      <main className="app-gate">
        {state.regionStatus === "error" ? (
          <div role="alert">
            <h1 className="panel-heading">The planning data for this region could not be loaded.</h1>
            <p>{state.regionError?.message}</p>
            <button className="btn btn-primary" onClick={m.loadRegion}>Retry</button>
          </div>
        ) : <p role="status">Loading the region…</p>}
      </main>
    );
  }

  const b = state.bundle, region = b.region;
  const [freshText, freshClass] = FRESH[state.freshness];
  const no3d = !webgl || !b.elevation;
  const view = no3d ? "2d" : state.view;
  const warnings = region.warnings;
  const onTabKey = (e: KeyboardEvent) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const tab = TABS[(TABS.indexOf(state.tab) + step + TABS.length) % TABS.length];
    dispatch({ type: "setTab", tab });
    document.getElementById(`tab-${tab}`)?.focus();
  };

  return (
    <div className={`app pane-${pane}${drawer ? " drawer-open" : ""}`}>
      <header className="bar">
        <button className="btn drawer-toggle" aria-expanded={drawer} onClick={() => setDrawer(!drawer)}>Plan</button>
        <span className="product">Mars Return / Excursion planner</span>
        {isSample(b) ? <span className="tag tag-sample">Development sample data</span>
          : <span className="tag">Real CTX terrain · Jezero Crater</span>}
        <details className="versions" open>
          <summary>Versions</summary>
          <span className="mono">Dataset {region.datasetVersion}</span>
          <span className="mono" title={state.plan?.planId}>Plan {state.plan ? state.plan.planId.slice(0, 8) : "—"}</span>
          <span className="mono">Model {state.plan?.modelVersion ?? "—"}</span>
        </details>
        <span className={`status ${freshClass} fresh`} aria-live="polite">{freshText}</span>
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
        <details className="limits">
          <summary>Model limits ({warnings.length})</summary>
          <ul>{warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </details>
      </aside>

      <main className="view" aria-label="Viewing area">
        <div className="toolbar">
          <div className="segments" role="group" aria-label="View">
            <button aria-pressed={view === "2d"} onClick={() => dispatch({ type: "setView", view: "2d" })}>2D map</button>
            <button aria-pressed={view === "3d"} disabled={no3d} aria-describedby={no3d ? "no3d" : undefined}
              onClick={() => dispatch({ type: "setView", view: "3d" })}>3D terrain</button>
          </div>
          <Layers m={m} />
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
          <button className="btn" disabled={!m.current} onClick={() => dispatch({ type: "setReport", open: true })}>Open mission report</button>
          {!m.current && <p className="reason">Request routes to enable. The report never exports an outdated result.</p>}
        </div>
      </aside>

      {m.current && m.points.length > 0 && <footer className="strip"><RehearsalStrip m={m} /></footer>}
      <MissionReport m={m} />
    </div>
  );
}
