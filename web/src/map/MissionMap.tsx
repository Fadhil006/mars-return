import { useMemo, type CSSProperties, type ReactNode } from "react";
import { num } from "../mission/format";
import { extentM, returnRetraces, routesIdentical } from "../mission/geo";
import type { Mission } from "../mission/state";
import { MODE_LABEL, type Mode, type RegionBundle, type XY } from "../mission/types";
import { arrowsAlong, blindRuns, calloutSide, cellMissing, CONTACT_FILL, contactCanvas, layerCanvas, SLOPE_BREAKS, SLOPE_COLORS } from "./layers";
import "./map.css";

const VIOLET = "var(--hypothetical)";

interface LineProps { pts: XY[] | null | undefined; toSvg: (p: XY) => string; color?: string; width?: number; dash?: string; casing?: boolean | string; opacity?: number; arrows?: ArrowSpec; reveal?: { id: string; delay?: number } }
interface ArrowSpec { size: number; offset: number; flipY: (p: XY) => [number, number] }

/** Three display-only arrowheads along a leg, pointing the way of travel; `offset` staggers legs that share a path. */
function Arrows({ pts, color = "var(--route)", spec }: { pts: XY[]; color?: string; spec: ArrowSpec }) {
  const s = spec.size;
  return arrowsAlong(pts, 3, spec.offset).map(({ at, heading }, i) => {
    const [x, y] = spec.flipY(at);
    return <polygon key={i} className="mm-arrow" points={`${s},0 ${-s},${0.8 * s} ${-0.4 * s},0 ${-s},${-0.8 * s}`}
      transform={`translate(${x} ${y}) rotate(${(-heading * 180) / Math.PI})`} style={{ fill: color }} />;
  });
}

/** A returned path drawn exactly as supplied: no smoothing, with a dark casing so it holds contrast over imagery. */
function Line({ pts, toSvg, color = "var(--route)", width = 3, dash, casing = true, opacity = 1, arrows, reveal }: LineProps) {
  if (!pts || pts.length < 2) return null;
  const points = pts.map(toSvg).join(" ");
  // Display only: a newly returned route is drawn along its own path once, start to end (instant under reduced motion).
  const maskId = reveal ? `mm-reveal-${reveal.id}` : undefined;
  return (
    <g opacity={opacity} mask={maskId ? `url(#${maskId})` : undefined}>
      {maskId && (
        <mask id={maskId} maskUnits="userSpaceOnUse" x="-1e5" y="-1e5" width="2e5" height="2e5">
          <polyline className="mm-reveal" points={points} pathLength={1} style={{ animationDelay: `${reveal!.delay ?? 0}ms` }} />
        </mask>
      )}
      {casing && <polyline className="mm-line" points={points} style={{ stroke: "var(--casing)", strokeWidth: width + 3 }}
        strokeDasharray={typeof casing === "string" ? casing : undefined} />}
      <polyline className="mm-line" points={points} style={{ stroke: color, strokeWidth: width }} strokeDasharray={dash} />
      {arrows && <Arrows pts={pts} color={color} spec={arrows} />}
    </g>
  );
}

function Swatch({ color, dash, fill }: { color?: string; dash?: boolean; fill?: string }) {
  const style: CSSProperties = fill ? { background: fill } : { borderTop: `3px ${dash ? "dashed" : "solid"} ${color}`, height: 0 };
  return <span className="mm-swatch" style={style} aria-hidden="true" />;
}

export function MissionMap({ m }: { m: Mission }) {
  return m.state.bundle ? <MapView m={m} bundle={m.state.bundle} /> : null;
}

function MapView({ m, bundle }: { m: Mission; bundle: RegionBundle }) {
  const { state } = m;
  const manifest = bundle.region.manifest;
  const [ox, oy] = manifest.originXY;
  const { w, h } = extentM(manifest);
  const { layers } = state;

  // The single map transform: local metres, north up. Every mark goes through one of these two.
  const toSvg = (p: XY) => `${p[0]},${oy + h - p[1]}`;
  const flipY = (p: XY): [number, number] => [p[0], oy + h - p[1]];
  const at = (p: XY): CSSProperties => ({ left: `${((p[0] - ox) / w) * 100}%`, top: `${((oy + h - p[1]) / h) * 100}%` });

  const reach = state.reach.data;
  const slopeUrl = useMemo(() => (layers.slope ? layerCanvas("slope", bundle)?.toDataURL() : undefined), [bundle, layers.slope]);
  const envelopeUrl = useMemo(() => (layers.envelope && reach ? layerCanvas("envelope", bundle, reach)?.toDataURL() : undefined), [bundle, reach, layers.envelope]);
  const contact = state.freshness === "current" ? state.plan?.contact : null;
  const contactUrl = useMemo(() => (layers.contact && contact ? contactCanvas(contact.visible)?.toDataURL() : undefined), [contact, layers.contact]);
  const missingUrl = useMemo(() => {
    for (let r = 0; r < manifest.height; r++)
      for (let c = 0; c < manifest.width; c++)
        if (cellMissing(bundle, r, c)) return layerCanvas("missing", bundle)?.toDataURL();
    return undefined;
  }, [bundle, manifest]);
  const grid = (href: string | undefined, opacity = 1) =>
    href && <image className="mm-grid" href={href} x={ox} y={0} width={w} height={h} preserveAspectRatio="none" opacity={opacity} />;

  // A plan that is not current is never shown as if it were: it is dimmed and labelled.
  const a = state.plan ? m.assessment : null;
  const outdated = !!a && state.freshness !== "current";
  const out = a?.outbound?.pathXY, back = a?.return?.pathXY;
  const retraces = !!a && returnRetraces(a);
  const otherMode: Mode = m.mode === "shortest" ? "slope_penalized" : "shortest";
  const other = m.current && state.plan && !routesIdentical(state.plan) ? state.plan.options[otherMode] : null;
  const routeOpacity = outdated ? 0.35 : state.rehearsing ? 0.55 : 1;
  // A new plan or mode re-runs the draw-in once; the same result never animates again.
  const revealKey = `${state.plan?.planId ?? "none"}-${m.mode}`.replace(/[^\w-]/g, "");
  const travelled = state.rehearsing && !outdated ? m.points.slice(0, m.posIndex + 1).map((p) => p.xy) : null;

  const ret = state.ret.data, stress = state.stress.data;
  const hatch = w / 100; // shortcut: hatch spacing is 1% of the map (6 px at 600 px wide), not a fixed 6 px; measure the element if exact spacing matters
  const barM = [5000, 2000, 1000, 500, 200, 100, 50].find((len) => len <= w / 4) ?? w / 4;
  const stopName = (id: string, name?: string) => name ?? id;
  const selectedStop = m.stop;
  const arrowSize = w / 85; // about 6 px half-length on a 500 px map
  const outArrows = { size: arrowSize, offset: 0.35, flipY }, backArrows = { size: arrowSize, offset: 0.65, flipY };

  /** A two-line callout joined to its marker by a leader (22 px across, 38 px up or down). */
  const frac = (p: XY): [number, number] => [(p[0] - ox) / w, (oy + h - p[1]) / h];
  const callout = (p: XY, side: { left: boolean; up: boolean }, title: string, sub: string, hidden?: boolean) => (
    <span className={`mm-callout ${side.left ? "mm-co-left" : "mm-co-right"} ${side.up ? "mm-co-up" : "mm-co-down"}`} style={at(p)} aria-hidden={hidden || undefined}>
      <svg className="mm-leader" aria-hidden="true"><line x1={0} y1={0} x2={side.left ? -22 : 22} y2={side.up ? -38 : 38} /></svg>
      <span className="mm-callout-box"><b>{title}</b><span>{sub}</span></span>
    </span>
  );
  const stopXY = layers.stops ? selectedStop?.positionXY : undefined;
  const baseSide = m.baseXY && calloutSide(frac(m.baseXY), stopXY && frac(stopXY));
  let stopSide = stopXY && calloutSide(frac(stopXY), m.baseXY && frac(m.baseXY));
  if (baseSide && stopSide && stopXY && m.baseXY && baseSide.left === stopSide.left && baseSide.up === stopSide.up
    && Math.abs(frac(stopXY)[0] - frac(m.baseXY)[0]) < 0.3 && Math.abs(frac(stopXY)[1] - frac(m.baseXY)[1]) < 0.15)
    stopSide = { ...stopSide, up: !stopSide.up }; // boxes would overlap: send the stop's the other way

  const legend: ReactNode[] = [];
  if (out && !outdated) legend.push(<li key="sel"><Swatch color="var(--route)" />Outbound · {MODE_LABEL[m.mode]}</li>);
  if (out && !outdated && back) legend.push(<li key="ret"><Swatch color="var(--route)" dash />Return{retraces ? " (same path, arrows show direction)" : ""}</li>);
  if (outdated) legend.push(<li key="old"><Swatch color="var(--status-outdated)" dash />Outdated route</li>);
  if (other) legend.push(<li key="other"><Swatch color="rgba(61,214,232,0.5)" />{MODE_LABEL[otherMode]} (not selected)</li>);
  if (ret) legend.push(
    <li key="now"><Swatch color={VIOLET} />Return now <span className="tag tag-hyp">Hypothetical</span></li>,
    <li key="cont"><Swatch color={VIOLET} dash />Continue, then return <span className="tag tag-hyp">Hypothetical</span></li>);
  if (m.corridor) legend.push(<li key="cor"><span className="mm-swatch mm-swatch-hatch" aria-hidden="true" />Blocked corridor <span className="tag tag-hyp">Hypothetical</span></li>);
  if (stress) legend.push(<li key="stress"><span className="mm-swatch mm-swatch-oct" aria-hidden="true" />Closure tested, {num(stress.closureRadiusM)} m (✕ = return fails) <span className="tag tag-hyp">Hypothetical</span></li>);
  if (contactUrl && contact) legend.push(<li key="contact"><Swatch fill={CONTACT_FILL} />Base cannot see here · {num(contact.mastHeightM)} m mast <span className="tag tag-hyp">Hypothetical</span></li>);
  if (contactUrl && !outdated && (a?.outOfContactMin ?? 0) > 0) legend.push(<li key="blind"><Swatch color="#0b1220" dash />Route out of sight of base</li>);
  if (envelopeUrl) legend.push(<li key="env"><Swatch fill="rgba(61,214,232,0.35)" />Return envelope · Hypothetical scenario</li>);
  if (layers.traverse && bundle.traverse) legend.push(<li key="trav"><Swatch color="#eef1f3" />Perseverance traverse (real rover path)</li>);
  if (missingUrl) legend.push(<li key="miss"><span className="mm-swatch mm-swatch-missing" aria-hidden="true" />No elevation data</li>);

  return (
    <div className="mm-wrap">
      <div className="mm" style={{ "--mm-ratio": w / h } as CSSProperties}>
        <svg className="mm-svg" viewBox={`${ox} 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <pattern id="mm-hatch" patternUnits="userSpaceOnUse" width={hatch} height={hatch} patternTransform="rotate(-45)">
              <line x1={0} y1={0} x2={0} y2={hatch} style={{ stroke: VIOLET, strokeWidth: hatch / 2 }} />
            </pattern>
          </defs>
          {layers.imagery && bundle.imageryUrl && <image className="mm-imagery" href={bundle.imageryUrl} x={ox} y={0} width={w} height={h} preserveAspectRatio="none" />}
          {grid(slopeUrl, 0.6)}
          {grid(contactUrl)}
          {grid(envelopeUrl)}
          {grid(missingUrl)}
          <rect className="mm-line" x={ox} y={0} width={w} height={h} style={{ stroke: "var(--border-control)", strokeWidth: 1 }} />

          {layers.traverse && <Line pts={bundle.traverse?.pathXY} toSvg={toSvg} color="#eef1f3" width={1} casing={false} opacity={0.8} />}

          {stress?.closures.map((c, i) => {
            const ok = c.status === "ok";
            const octagon = Array.from({ length: 8 }, (_, k): XY => [
              c.centerXY[0] + stress.closureRadiusM * Math.cos((k * Math.PI) / 4),
              c.centerXY[1] + stress.closureRadiusM * Math.sin((k * Math.PI) / 4)]);
            return (
              <g key={i}>
                <Line pts={c.pathXY} toSvg={toSvg} color={VIOLET} width={1.5} dash="2 4" casing={false} />
                <polygon className="mm-line" points={octagon.map(toSvg).join(" ")} strokeDasharray={ok ? undefined : "4 3"}
                  style={{ stroke: ok ? VIOLET : "var(--status-error)", strokeWidth: 2 }} />
              </g>
            );
          })}

          {other && <Line pts={other.outbound?.pathXY} toSvg={toSvg} width={1.5} casing={false} opacity={0.4} />}
          {other && !returnRetraces(other) && <Line pts={other.return?.pathXY} toSvg={toSvg} width={1.5} casing={false} opacity={0.4} />}

          <Line key={`out-${revealKey}`} pts={out} toSvg={toSvg} opacity={routeOpacity} casing={outdated ? "6 4" : true} arrows={outdated ? undefined : outArrows}
            reveal={outdated ? undefined : { id: `out-${revealKey}` }} />
          {!retraces && <Line key={`back-${revealKey}`} pts={back} toSvg={toSvg} dash="8 6" opacity={routeOpacity} casing={outdated ? "6 4" : true} arrows={outdated ? undefined : backArrows}
            reveal={outdated ? undefined : { id: `back-${revealKey}`, delay: 700 }} />}
          {contactUrl && !outdated && [a?.outbound, a?.return].flatMap((leg, k) => blindRuns(leg?.pathXY, leg?.inContact).map((run, i) =>
            <Line key={`blind-${k}-${i}`} pts={run} toSvg={toSvg} color="#0b1220" width={3} dash="3 5" casing={false} opacity={routeOpacity} />))}
          {retraces && back && !outdated && <g opacity={routeOpacity}><Arrows pts={back} spec={backArrows} /></g>}
          <Line pts={travelled} toSvg={toSvg} />

          {m.corridor && (
            <g>
              <polygon points={m.corridor.map(toSvg).join(" ")} fill="url(#mm-hatch)" stroke="none" />
              <polygon className="mm-line" points={m.corridor.map(toSvg).join(" ")} style={{ stroke: "var(--casing)", strokeWidth: 4 }} />
              <polygon className="mm-line" points={m.corridor.map(toSvg).join(" ")} style={{ stroke: VIOLET, strokeWidth: 2 }} />
            </g>
          )}

          {ret && <Line pts={ret.immediateReturn.return?.pathXY} toSvg={toSvg} color={VIOLET} />}
          {ret && <Line pts={ret.continueThenReturn.currentToTarget?.pathXY} toSvg={toSvg} color={VIOLET} dash="8 6" />}
          {ret && <Line pts={ret.continueThenReturn.targetToBase?.pathXY} toSvg={toSvg} color={VIOLET} dash="8 6" />}
        </svg>

        {/* Markers and labels are HTML so text stays 12 px and stops are real buttons for keyboard and screen readers. */}
        <div className="mm-overlay">
          {stress?.closures.filter((c) => c.status !== "ok").map((c, i) => (
            <span key={i} className="mm-fail" style={at(c.centerXY)} aria-hidden="true">✕</span>
          ))}
          {/* Below the corridor's south edge so it never sits under the current-position label above the route. */}
          {m.corridor && <span className="mm-label mm-label-hyp mm-below" style={at([(m.corridor[0][0] + m.corridor[1][0]) / 2, m.corridor[0][1]])}>Hypothetical</span>}
          {outdated && out && <span className="mm-label mm-label-outdated" style={at(out[Math.floor(out.length / 2)])}>Outdated</span>}

          {m.baseXY && <span className="mm-mark mm-base" style={at(m.baseXY)} aria-hidden="true" />}
          {m.baseXY && baseSide && callout(m.baseXY, baseSide, "Base", "Hypothetical base")}
          {selectedStop && stopXY && stopSide && callout(stopXY, stopSide, stopName(selectedStop.id, selectedStop.name).split(" — ")[0], "Perseverance sampling site", true)}

          {layers.stops && bundle.region.scienceStops.map((stop) => {
            const selected = stop.id === state.inputs.targetId;
            return (
              <button key={stop.id} type="button" className={`mm-stop${selected ? " mm-stop-selected" : ""}${layers.labels ? " mm-stop-labelled" : ""}`} style={at(stop.positionXY)}
                aria-pressed={selected} aria-label={`Select destination ${stopName(stop.id, stop.name)}`}
                disabled={state.rehearsing} title={state.rehearsing ? "Edit the plan to change destination" : undefined}
                onClick={() => m.pickStop(stop.id)}>
                <span className="mm-label">{stopName(stop.id, stop.name).split(" — ")[0]}</span>
              </button>
            );
          })}

          {state.rehearsing && m.point && !outdated && (
            <span className="mm-mark mm-pos" style={at(m.point.xy)}><span className="mm-label">Current position</span></span>
          )}

          <div className="mm-north" role="img" aria-label="North is up">
            N<svg width="16" height="20" viewBox="0 0 16 20" aria-hidden="true"><path d="M8 1 L15 19 L8 14 L1 19 Z" /></svg>
          </div>

          <div className="mm-br">
            {retraces && !outdated && <span className="mm-label">Return follows the outbound path</span>}
            {!bundle.imageryUrl && <span className="mm-label mm-label-warn" role="status">Imagery could not be loaded; marks are drawn on a plain background</span>}
            {bundle.missing.includes("mask.json") && (
              <span className="mm-label mm-label-warn" role="status">
                The missing-data mask could not be loaded; gaps are shown only where elevation is missing
              </span>
            )}
            <div className="mm-scale" style={{ width: `${(barM / w) * 100}cqw` }}>
              {[0, barM / 2, barM].map((v, i) => (
                <span key={i} style={{ left: `${i * 50}%` }}>{barM >= 1000 ? (i ? `${v / 1000}${i === 2 ? " km" : ""}` : "0") : `${v}${i === 2 ? " m" : ""}`}</span>
              ))}
            </div>
            {layers.imagery && bundle.imageryUrl && <span className="mm-caption">Imagery: {num(manifest.layerInfo?.imagery?.resolutionM ?? manifest.cellSizeM)} m pixels · terrain: {num(manifest.cellSizeM)} m cells<br />Greyscale CTX image, warm display tint</span>}
          </div>

          <details className="mm-legend" key={state.rehearsing ? "r" : "p"} open={!state.rehearsing}>
            <summary>Legend</summary>
            <ul>
              {legend}
              {layers.stops && <li><span className="mm-swatch mm-swatch-stop" aria-hidden="true" />Sampling site (filled = selected)</li>}
            </ul>
            {slopeUrl && (
              <div className="mm-slope">
                <span>Slope, derived from elevation</span>
                <ol>
                  {SLOPE_COLORS.map((color, i) => (
                    <li key={color}><Swatch fill={color} />
                      {i === 0 ? `< ${SLOPE_BREAKS[0]}°` : i === SLOPE_BREAKS.length ? `≥ ${SLOPE_BREAKS[i - 1]}°` : `${SLOPE_BREAKS[i - 1]}–${SLOPE_BREAKS[i]}°`}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </details>
        </div>

        <p className="sr-only">
          Map of the planning region, {num(w)} by {num(h)} metres, north up.{" "}
          {selectedStop ? `Selected destination: ${stopName(selectedStop.id, selectedStop.name)}. ` : ""}
          {out
            ? `${outdated ? "Outdated route shown" : "Route shown"}: ${MODE_LABEL[m.mode]}, ${num(a?.totalDistanceM)} metres in total.${retraces ? " The return follows the outbound path." : ""}`
            : "No route is drawn."}
          {m.corridor ? " A hypothetical blocked corridor is shown on the remaining path." : ""}
          {" "}The route metrics table gives the same information as text.
        </p>
      </div>
    </div>
  );
}
