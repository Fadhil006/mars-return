import type { PointerEvent } from "react";
import { num } from "./format";
import type { Assessment } from "./types";

export interface ProfilePoint { d: number; e: number }

/** Returned samples of both legs in travel order; index i matches routePoints(a)[i]. No smoothing or interpolation. */
export function profilePoints(a: Assessment | null | undefined): ProfilePoint[] {
  const out = a?.outbound?.profile, back = a?.return?.profile;
  if (!out || !back) return [];
  const offset = a!.outbound!.distanceM ?? 0;
  return [...out.map((s) => ({ d: s.distanceM, e: s.elevationM })), ...back.map((s) => ({ d: offset + s.distanceM, e: s.elevationM }))];
}

/** Index of the sample closest to distance d (metres along the round trip). */
export function nearestIndex(pts: { d: number }[], d: number): number {
  let best = 0;
  pts.forEach((p, i) => { if (Math.abs(p.d - d) < Math.abs(pts[best].d - d)) best = i; });
  return best;
}

const km = (m: number) => `${num(m / 1000, 1)} km`;
const metres = (m: number) => `${num(m)} m`.replace("-", "−");

interface Props {
  assessment: Assessment;
  posIndex: number;
  stopName: string;
  onSeek?: (index: number) => void; // absent while not rehearsing
}

export function ElevationProfile({ assessment, posIndex, stopName, onSeek }: Props) {
  const pts = profilePoints(assessment);
  if (pts.length < 2) return null;
  const total = pts[pts.length - 1].d || 1;
  const turn = assessment.outbound!.profile!.length - 1;
  const es = pts.map((p) => p.e);
  const lo = Math.min(...es), hi = Math.max(...es), span = hi - lo || 1;
  // Plot spans 12–88 % of the height so markers and labels stay inside the box.
  const X = (d: number) => (d / total) * 100;
  const Y = (e: number) => 88 - ((e - lo) / span) * 76;
  const line = pts.map((p) => `${X(p.d) * 10},${Y(p.e)}`).join(" ");
  const cur = pts[Math.min(posIndex, pts.length - 1)];
  const at = (p: ProfilePoint) => ({ left: `${X(p.d)}%`, top: `${Y(p.e)}%` });

  const seek = (e: PointerEvent<HTMLDivElement>) => {
    if (!onSeek || (e.type === "pointermove" && !e.buttons)) return;
    const r = e.currentTarget.getBoundingClientRect();
    onSeek(nearestIndex(pts, ((e.clientX - r.left) / r.width) * total));
  };

  return (
    <div className="ep" role="img"
      aria-label={`Elevation profile of the returned round trip: ${km(total)}, elevation ${metres(lo)} to ${metres(hi)}. Values are in the Routes table.`}>
      <div className="ep-y">
        <span style={{ top: `${Y(hi)}%` }}>{metres(hi)}</span>
        <span style={{ top: `${Y((hi + lo) / 2)}%` }}>{metres((hi + lo) / 2)}</span>
        <span style={{ top: `${Y(lo)}%` }}>{metres(lo)}</span>
      </div>
      <div className={`ep-plot${onSeek ? " ep-seek" : ""}`}
        onPointerDown={(e) => { if (onSeek) { e.currentTarget.setPointerCapture(e.pointerId); seek(e); } }} onPointerMove={seek}>
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id="ep-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="var(--action)" stopOpacity="0.35" />
              <stop offset="1" stopColor="var(--action)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <polygon points={`0,100 ${line} 1000,100`} fill="url(#ep-fill)" />
          <polyline points={line} className="ep-line" />
          <line x1={X(pts[turn].d) * 10} x2={X(pts[turn].d) * 10} y1="0" y2="100" className="ep-turn" />
          <line x1={X(cur.d) * 10} x2={X(cur.d) * 10} y1="0" y2="100" className="ep-cursor" />
        </svg>
        <span className="ep-mark ep-base" style={at(pts[0])} />
        <span className="ep-mark ep-stop" style={at(pts[turn])} />
        <span className="ep-mark ep-base" style={at(pts[pts.length - 1])} />
        <span className="ep-mark ep-pos" style={at(cur)} />
        <span className="ep-label" style={{ left: 0 }}><b>Base</b> ({km(0)})</span>
        <span className="ep-label ep-mid" style={{ left: `${X(pts[turn].d)}%` }}><b>{stopName}</b> ({km(pts[turn].d)})</span>
        <span className="ep-label ep-end" style={{ right: 0 }}><b>Base</b> ({km(total)})</span>
      </div>
    </div>
  );
}
