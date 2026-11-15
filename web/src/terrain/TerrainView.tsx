import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";
import { layerCanvas } from "../map/layers";
import { extentM, returnRetraces } from "../mission/geo";
import type { Mission } from "../mission/state";
import type { XY } from "../mission/types";
import { MAX_TILT, autoRelief, heightfield, skirtPositions, surfacePoint } from "./scene";
import "./terrain.css";

const ROUTE = 0x3dd6e8, HYPOTHETICAL = 0xc9a0ff, WHITE = 0xffffff, CASING = 0x0b1114, WALL = 0x2a201b;
const LIFT_M = 3; // display-only offset that keeps lines from flickering against the surface
const CONTOUR_M = 10; // contour interval in measured metres; drawn from the elevation, never from the image
const EXAGGERATIONS = [1, 2, 5] as const; // display only; Auto (tilt-driven) is the default and every value drawn is labelled
// Raking light from the north-west (azimuth 315°, 25° above the horizon), the usual hillshade convention:
// low light is what makes small real relief readable. Display only; it is not the image's own sun.
const SUN_AZIMUTH = (315 * Math.PI) / 180, SUN_ALTITUDE = (25 * Math.PI) / 180;

/** Adds elevation contours to a standard material. Height is the mesh's own Y (measured metres, before exaggeration). */
function withContours(material: THREE.MeshStandardMaterial, uniforms: { uContours: { value: number } }) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uContours = uniforms.uContours;
    shader.uniforms.uInterval = { value: CONTOUR_M };
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying float vHeight;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvHeight = position.y;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying float vHeight;\nuniform float uContours;\nuniform float uInterval;")
      .replace("#include <map_fragment>", `#include <map_fragment>
        float hc = vHeight / uInterval;
        float line = 1.0 - min(abs(fract(hc - 0.5) - 0.5) / max(fwidth(hc), 1e-4), 1.0);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.97, 0.93, 0.86), line * 0.55 * uContours);`);
  };
}

let webgl: boolean | undefined;
/** False when this browser cannot create a WebGL context; the 3D toggle is then disabled. */
export function webglAvailable(): boolean {
  if (webgl === undefined) {
    try {
      const canvas = document.createElement("canvas");
      webgl = !!(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
    } catch {
      webgl = false;
    }
  }
  return webgl;
}

interface Ctx {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  material: THREE.MeshStandardMaterial;
  mesh: THREE.Mesh;
  walls: THREE.Mesh;
  contours: { uContours: { value: number } };
  groups: Record<"route" | "marks" | "corridor" | "ret", THREE.Group>;
  origin: number;
  render: () => void;
  reset: () => void;
}

function dispose(root: THREE.Object3D) {
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    mesh.geometry?.dispose();
    for (const mat of [mesh.material].flat()) {
      (mat as THREE.MeshLambertMaterial | undefined)?.map?.dispose();
      mat?.dispose();
    }
  });
}

function clear(group: THREE.Group) {
  dispose(group);
  group.clear();
}

export function TerrainView({ m }: { m: Mission }) {
  const { state } = m, { bundle, layers } = state;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const northRef = useRef<HTMLSpanElement>(null);
  const ctxRef = useRef<Ctx | null>(null);
  // HTML labels for the base and science stops, pinned to scene points on every render (stops are real buttons).
  const labelEls = useRef(new Map<string, HTMLElement>());
  const anchors = useRef(new Map<string, THREE.Vector3>());
  const [lost, setLost] = useState(false);
  const [exag, setExag] = useState(1); // display-only vertical exaggeration; always stated on the toggle and in the legend
  const [auto, setAuto] = useState(true); // relief follows camera tilt (autoRelief); the drawn value is always shown
  const autoRef = useRef(auto);
  autoRef.current = auto;
  const [contours, setContours] = useState(true);
  const usable = !!bundle?.elevation && webglAvailable() && !lost;

  const point = (xy: XY, lift = LIFT_M) => {
    const p = ctxRef.current && surfacePoint(bundle!, xy, ctxRef.current.origin);
    return p ? new THREE.Vector3(p[0], p[1] * exag + lift, p[2]) : null;
  };
  // Design 13.7: a 3 px line over a 6 px dark casing so it holds contrast over the imagery (screen-space widths).
  const addLine = (group: THREE.Group, path: XY[] | null | undefined, color: number, opacity = 1, dashed = false) => {
    const points = (path ?? []).map((xy) => point(xy)).filter((p) => p !== null);
    if (points.length < 2) return;
    const flat = points.flatMap((p) => [p.x, p.y, p.z]);
    for (const [c, linewidth, dash, order] of [[CASING, 6, false, 1], [color, 3, dashed, 2]] as const) {
      const line = new Line2(new LineGeometry().setPositions(flat), new LineMaterial({ color: c, linewidth, opacity,
        transparent: opacity < 1, dashed: dash, dashSize: 40, gapSize: 30 }));
      line.computeLineDistances();
      line.renderOrder = order;
      group.add(line);
    }
  };
  const addMark = (group: THREE.Group, geometry: THREE.BufferGeometry, xy: XY, color: number, lift: number, onTop = false) => {
    const position = point(xy, lift);
    if (!position) return geometry.dispose();
    const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color, depthTest: !onTop, side: THREE.DoubleSide }));
    mesh.position.copy(position);
    mesh.renderOrder = onTop ? 10 : 0;
    group.add(mesh);
  };

  // Scene, mesh and camera: once per region bundle.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!usable || !canvas || !bundle) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    } catch {
      setLost(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0); // the CSS backdrop behind the canvas is a plain gradient, not terrain
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const scene = new THREE.Scene();

    const field = heightfield(bundle);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(field.positions, 3));
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(field.uvs, 2));
    geometry.setIndex(field.indices);
    geometry.computeVertexNormals();
    const contourUniforms = { uContours: { value: 1 } };
    const material = new THREE.MeshStandardMaterial({ color: 0x8a8580, roughness: 0.95, metalness: 0, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    withContours(material, contourUniforms);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = mesh.receiveShadow = true; // relief shades itself: crater rims and scarps cast real-geometry shadows
    scene.add(mesh);

    const manifest = bundle.region.manifest, { w, h } = extentM(manifest), span = Math.max(w, h);
    geometry.computeBoundingBox();
    const relief = geometry.boundingBox!.max.y;
    // Block sides: the measured edge profile carried down to a base below the lowest cell (display only).
    const wallGeometry = new THREE.BufferGeometry();
    wallGeometry.setAttribute("position", new THREE.Float32BufferAttribute(skirtPositions(field, -Math.max(40, relief * 0.4)), 3));
    wallGeometry.computeVertexNormals();
    const walls = new THREE.Mesh(wallGeometry, new THREE.MeshStandardMaterial({ color: WALL, roughness: 1, side: THREE.DoubleSide }));
    scene.add(walls);

    // Dim sky/ground fill plus one raking sun; low fill keeps the shading from the real slopes visible.
    scene.add(new THREE.HemisphereLight(0xd8dde3, 0x3a2a22, 0.7));
    const sun = new THREE.DirectionalLight(0xfff4e8, 3.4);
    const d = span * 1.5;
    sun.position.set(-Math.sin(-SUN_AZIMUTH) * Math.cos(SUN_ALTITUDE) * d, Math.sin(SUN_ALTITUDE) * d, -Math.cos(SUN_AZIMUTH) * Math.cos(SUN_ALTITUDE) * d);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 1, far: d * 3 });
    sun.shadow.bias = -0.0005;
    sun.shadow.normalBias = span / 600;

    const groups = { route: new THREE.Group(), marks: new THREE.Group(), corridor: new THREE.Group(), ret: new THREE.Group() };
    scene.add(...Object.values(groups));

    const centre = new THREE.Vector3(manifest.originXY[0] + w / 2, relief / 2, -(manifest.originXY[1] + h / 2));
    sun.position.add(centre);
    sun.target.position.copy(centre);
    scene.add(sun, sun.target);
    const camera = new THREE.PerspectiveCamera(45, 1, span / 500, span * 10);
    const controls = new OrbitControls(camera, canvas); // no damping: every camera move is immediate
    controls.maxPolarAngle = MAX_TILT;
    controls.minDistance = span / 20;
    controls.maxDistance = span * 3;
    const render = () => {
      renderer.render(scene, camera);
      const { clientWidth: cw, clientHeight: ch } = canvas;
      const placed: { x: number; y: number; w: number; h: number }[] = [];
      const items = [...labelEls.current].map(([id, el]) => ({ el, v: anchors.current.get(id)?.clone().project(camera) }))
        .sort((a, b) => (b.v?.y ?? 0) - (a.v?.y ?? 0)); // nearest the top first, so a clash pushes the lower label up past it
      for (const { el, v } of items) {
        // shortcut: labels are not hidden behind terrain, only behind the camera; raycast if ridges ever hide a stop.
        el.hidden = !v || v.z > 1 || Math.abs(v.x) > 1 || Math.abs(v.y) > 1;
        if (!v || el.hidden) continue;
        const box = { x: ((v.x + 1) / 2) * cw - el.offsetWidth / 2, y: ((1 - v.y) / 2) * ch - (el.classList.contains("terrain-stop-dot") ? el.offsetHeight / 2 : el.offsetHeight + 14), w: el.offsetWidth, h: el.offsetHeight };
        // Overlapping labels stack upward so every stop stays readable and clickable.
        for (const o of placed) if (box.x < o.x + o.w && o.x < box.x + box.w && box.y < o.y + o.h && o.y < box.y + box.h) box.y = o.y - box.h - 2;
        placed.push(box);
        el.style.transform = `translate(${box.x}px, ${box.y}px)`;
      }
      if (northRef.current) northRef.current.style.transform = `rotate(${controls.getAzimuthalAngle()}rad)`;
    };
    const reset = () => {
      controls.target.copy(centre);
      // From the south-east, about 30° above the horizon, far enough back that the whole block and its near sides are in frame.
      const fit = (0.75 * span) / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) / Math.min(1, Math.max(camera.aspect, 0.75));
      camera.position.copy(centre).add(new THREE.Vector3(0.82, 0.68, 0.82).normalize().multiplyScalar(fit * 0.85));
      controls.update();
      render();
    };
    controls.addEventListener("change", render);
    controls.addEventListener("change", () => { if (autoRef.current) setExag(autoRelief(controls.getPolarAngle())); });
    const onLost = (event: Event) => { event.preventDefault(); setLost(true); };
    canvas.addEventListener("webglcontextlost", onLost);
    const observer = new ResizeObserver(() => {
      const { clientWidth, clientHeight } = canvas.parentElement!;
      if (!clientWidth || !clientHeight) return;
      renderer.setSize(clientWidth, clientHeight, false);
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      render();
    });
    observer.observe(canvas.parentElement!);

    ctxRef.current = { renderer, scene, camera, controls, material, mesh, walls, contours: contourUniforms, groups, origin: field.origin, render, reset };
    reset();
    return () => {
      ctxRef.current = null;
      observer.disconnect();
      canvas.removeEventListener("webglcontextlost", onLost);
      controls.dispose();
      dispose(scene);
      renderer.dispose();
    };
  }, [bundle, usable]);

  useEffect(() => {
    const ctx = ctxRef.current;
    if (auto && ctx) setExag(autoRelief(ctx.controls.getPolarAngle()));
  }, [bundle, usable, auto]);

  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    ctx.mesh.scale.y = ctx.walls.scale.y = exag;
    ctx.contours.uContours.value = contours ? 1 : 0;
    ctx.render();
  }, [bundle, usable, exag, contours]);

  // Surface texture: imagery plus the grid layers that are switched on.
  const reach = state.reach.data;
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx || !bundle) return;
    const manifest = bundle.region.manifest;
    const canvas = document.createElement("canvas");
    canvas.width = manifest.width * 4;
    canvas.height = manifest.height * 4;
    const g = canvas.getContext("2d")!;
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const paint = (image: HTMLImageElement | null) => {
      g.globalAlpha = 1;
      g.fillStyle = "#8a8580"; // neutral surface when imagery is off or unavailable
      g.fillRect(0, 0, canvas.width, canvas.height);
      if (image) {
        // Same warm display tint as the 2D map (styles.css --mars-tint); the CTX image itself is greyscale.
        g.filter = getComputedStyle(document.documentElement).getPropertyValue("--mars-tint").trim() || "none";
        g.drawImage(image, 0, 0, canvas.width, canvas.height);
        g.filter = "none";
      }
      const slope = layers.slope ? layerCanvas("slope", bundle) : null;
      const envelope = layers.envelope && reach ? layerCanvas("envelope", bundle, reach) : null;
      g.imageSmoothingEnabled = false;
      if (slope) { g.globalAlpha = 0.6; g.drawImage(slope, 0, 0, canvas.width, canvas.height); }
      if (envelope) { g.globalAlpha = 1; g.drawImage(envelope, 0, 0, canvas.width, canvas.height); }
      g.imageSmoothingEnabled = true;
      texture.needsUpdate = true;
      ctx.render();
    };
    ctx.material.map?.dispose();
    ctx.material.map = texture;
    ctx.material.color.set(WHITE);
    ctx.material.needsUpdate = true;
    paint(null);
    let cancelled = false;
    if (layers.imagery && bundle.imageryUrl) {
      const image = new Image();
      image.onload = () => { if (!cancelled && ctxRef.current === ctx) paint(image); };
      image.src = bundle.imageryUrl;
    }
    return () => { cancelled = true; };
  }, [bundle, usable, layers.imagery, layers.slope, layers.envelope, reach]);

  // Route and current position. Playback only touches this group, never the mesh.
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    clear(ctx.groups.route);
    const fresh = state.freshness === "current";
    const split = fresh && state.rehearsing;
    const part = (leg: "outbound" | "return", from: number, to: number, opacity: number) => addLine(ctx.groups.route,
      m.points.slice(from, to).filter((p) => p.leg === leg).map((p) => p.xy), ROUTE, opacity, leg === "return");
    for (const leg of ["outbound", "return"] as const) {
      // Where the return retraces the outbound path one line is drawn, not a fabricated second one.
      if (leg === "return" && !split && m.assessment && returnRetraces(m.assessment)) continue;
      if (split) {
        part(leg, 0, m.posIndex + 1, 1);
        part(leg, m.posIndex, m.points.length, 0.55);
      } else {
        part(leg, 0, m.points.length, fresh ? 1 : 0.35); // dimmed when outdated
      }
    }
    if (split && m.point) addMark(ctx.groups.route, new THREE.OctahedronGeometry(22), m.point.xy, ROUTE, 30, true);
    const at = split && state.playing && m.point ? point(m.point.xy, 0) : null;
    if (at) { // while playing, the camera travels with the current position; orbit and zoom still work
      ctx.camera.position.add(at.clone().sub(ctx.controls.target));
      ctx.controls.target.copy(at);
      ctx.controls.update();
    }
    ctx.render();
  }, [bundle, usable, exag, m.assessment, state.freshness, state.rehearsing, state.playing, m.posIndex]);

  // When a new plan arrives, glide the camera to frame its route (same viewing direction; instant under reduced motion).
  // Also runs when the 3D view opens; never while playback is moving the camera itself.
  const planId = state.freshness === "current" ? state.plan?.planId : undefined;
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx || !planId || state.playing || m.points.length < 2) return;
    const pts = m.points.map((p) => point(p.xy, 0)).filter((p) => p !== null);
    if (pts.length < 2) return;
    const box = new THREE.Box3().setFromPoints(pts);
    const target = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3()).length();
    const span = Math.max(...Object.values(extentM(bundle!.region.manifest)));
    const dir = ctx.camera.position.clone().sub(ctx.controls.target).normalize();
    const dist = THREE.MathUtils.clamp(size * 1.6, span / 4, span * 1.2);
    const toPos = target.clone().add(dir.multiplyScalar(dist));
    const fromPos = ctx.camera.position.clone(), fromTarget = ctx.controls.target.clone();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const duration = reduce ? 0 : 1100, start = performance.now();
    let frame = 0;
    const step = (now: number) => {
      const t = duration ? Math.min(1, (now - start) / duration) : 1, e = 1 - Math.pow(1 - t, 3); // ease-out cubic
      ctx.camera.position.lerpVectors(fromPos, toPos, e);
      ctx.controls.target.lerpVectors(fromTarget, target, e);
      ctx.controls.update();
      ctx.render();
      if (t < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [planId, m.mode, usable]); // eslint-disable-line react-hooks/exhaustive-deps

  // Base, science stops and the rover traverse.
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx || !bundle) return;
    const group = ctx.groups.marks;
    clear(group);
    anchors.current.clear();
    const anchor = (id: string, xy: XY) => { const p = point(xy, 13); if (p) anchors.current.set(id, p); };
    if (m.baseXY) anchor("base", m.baseXY);
    if (layers.stops) for (const stop of bundle.region.scienceStops) anchor(stop.id, stop.positionXY);
    if (m.baseXY) addMark(group, new THREE.BoxGeometry(28, 28, 28), m.baseXY, WHITE, 14);
    if (layers.stops) for (const stop of bundle.region.scienceStops) {
      addMark(group, new THREE.SphereGeometry(13, 16, 12), stop.positionXY, WHITE, 13);
      if (stop.id === state.inputs.targetId) {
        addMark(group, new THREE.RingGeometry(24, 32, 32).rotateX(-Math.PI / 2), stop.positionXY, ROUTE, 5, true);
      }
    }
    if (layers.traverse) addLine(group, bundle.traverse?.pathXY, 0xb3bcc4, 0.8);
    ctx.render();
  }, [bundle, usable, exag, layers.stops, layers.traverse, state.inputs.targetId, m.baseXY]);

  // Hypothetical blocked corridor, draped by sampling each edge at cell spacing.
  const corridorKey = m.corridor ? m.corridor.flat().join() : "";
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx || !bundle) return;
    clear(ctx.groups.corridor);
    if (m.corridor) {
      const cell = bundle.region.manifest.cellSizeM, outline: XY[] = [];
      m.corridor.forEach((a, i) => {
        const b = m.corridor![(i + 1) % m.corridor!.length];
        const steps = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / cell));
        for (let k = 0; k < steps; k++) outline.push([a[0] + ((b[0] - a[0]) * k) / steps, a[1] + ((b[1] - a[1]) * k) / steps]);
      });
      outline.push(m.corridor[0]);
      // shortcut: outline only, no draped hatch fill; add a hatched surface patch if the corridor is hard to see in 3D.
      addLine(ctx.groups.corridor, outline, HYPOTHETICAL);
    }
    ctx.render();
  }, [bundle, usable, exag, corridorKey]);

  // Return options from the matching rehearsal result only.
  const ret = state.ret.data;
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    clear(ctx.groups.ret);
    if (ret) {
      addLine(ctx.groups.ret, ret.immediateReturn.return?.pathXY, HYPOTHETICAL);
      addLine(ctx.groups.ret, ret.continueThenReturn.currentToTarget?.pathXY, HYPOTHETICAL, 1, true);
      addLine(ctx.groups.ret, ret.continueThenReturn.targetToBase?.pathXY, HYPOTHETICAL, 1, true);
    }
    ctx.render();
  }, [bundle, usable, exag, ret]);

  if (!usable) {
    return (
      <div className="terrain terrain-unavailable" role="status">
        <p className="prose">
          {bundle && !bundle.elevation
            ? "No elevation data could be loaded, so 3D terrain cannot be drawn. The 2D map has the same route and controls."
            : "3D terrain is not available in this browser. The 2D map has the same route and controls."}
        </p>
      </div>
    );
  }

  const onKeyDown = (event: KeyboardEvent<HTMLCanvasElement>) => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    const offset = ctx.camera.position.clone().sub(ctx.controls.target);
    const s = new THREE.Spherical().setFromVector3(offset);
    switch (event.key) {
      case "ArrowLeft": s.theta -= 0.1; break;
      case "ArrowRight": s.theta += 0.1; break;
      case "ArrowUp": s.phi -= 0.08; break;
      case "ArrowDown": s.phi += 0.08; break;
      case "+": case "=": s.radius *= 0.9; break;
      case "-": case "_": s.radius *= 1.1; break;
      default: return;
    }
    event.preventDefault();
    s.phi = Math.min(Math.max(s.phi, 0.05), ctx.controls.maxPolarAngle);
    s.radius = Math.min(Math.max(s.radius, ctx.controls.minDistance), ctx.controls.maxDistance);
    ctx.camera.position.copy(ctx.controls.target).add(offset.setFromSpherical(s));
    ctx.controls.update();
    ctx.render();
  };

  return (
    <div className="terrain">
      <canvas ref={canvasRef} tabIndex={0} onKeyDown={onKeyDown}
        aria-label={`3D terrain from elevation data at ${exag === 1 ? "true vertical scale" : `${exag}× exaggerated vertical scale`}, with the same route and markers as the 2D map. Arrow keys orbit, plus and minus zoom.`} />
      <div className="terrain-marks">
        {m.baseXY && layers.labels && <span className="terrain-mark" ref={(el) => { if (el) labelEls.current.set("base", el); else labelEls.current.delete("base"); }}>Base · Hypothetical</span>}
        {layers.stops && bundle.region.scienceStops.map((stop) => {
          const selected = stop.id === state.inputs.targetId, name = (stop.name ?? stop.id).split(" — ")[0];
          return (
            <button key={stop.id} type="button" className={`terrain-mark terrain-stop${layers.labels ? "" : " terrain-stop-dot"}`} aria-pressed={selected}
              ref={(el) => { if (el) labelEls.current.set(stop.id, el); else labelEls.current.delete(stop.id); }}
              aria-label={`Select destination ${stop.name ?? stop.id}`} disabled={state.rehearsing}
              title={state.rehearsing ? "Edit the plan to change destination" : `Go to ${stop.name ?? stop.id}`}
              onClick={() => m.pickStop(stop.id)}>{layers.labels ? name : <span className="sr-only">{name}</span>}</button>
          );
        })}
      </div>
      <div className="terrain-info">
        <div className={`terrain-plate terrain-exag${exag > 1 ? " is-exag" : ""}`} role="group"
          aria-label="Vertical scale. Display only; no route value changes."
          title="Vertical scale. Display only; no route value changes.">
          <span className="terrain-exag-label">{auto ? `Auto ${exag}×` : exag === 1 ? "True scale" : "Exaggerated"}</span>
          <button type="button" aria-pressed={auto} onClick={() => setAuto(true)}
            title="Relief rises as you tilt toward the horizon; true scale from straight above">Auto</button>
          {EXAGGERATIONS.map((x) => (
            <button key={x} type="button" aria-pressed={!auto && exag === x} onClick={() => { setAuto(false); setExag(x); }}>{x}×</button>
          ))}
        </div>
        <button type="button" className="terrain-plate terrain-toggle" aria-pressed={contours}
          onClick={() => setContours(!contours)}>Contours {CONTOUR_M} m</button>
        <span className="terrain-plate terrain-north"><span ref={northRef} aria-hidden="true">↑</span> N</span>
      </div>
      <details className="terrain-legend terrain-plate">
      <summary>Legend</summary>
      <ul aria-label="3D marks">
        <li>■ Base · Hypothetical</li>
        {layers.stops && <li>● Science stop</li>}
        {m.points.length > 0 && <li><span className="terrain-route">━</span> Outbound <span className="terrain-route">┅</span> Return{state.freshness !== "current" && " · Outdated"}</li>}
        {state.rehearsing && <li><span className="terrain-route">◆</span> Current position</li>}
        {(m.corridor || ret) && <li><span className="terrain-hyp">━</span> Hypothetical scenario</li>}
        <li>Gaps: no elevation data{bundle.missing.includes("mask.json") && " (missing-data mask unavailable; other gaps not shown)"}</li>
        {exag > 1 && <li className="terrain-warn">Relief drawn {exag}× taller than measured</li>}
        {contours && <li>Contours every {CONTOUR_M} m, from elevation</li>}
        <li>Shading: light from the north-west, display only</li>
        <li>Block sides: measured edge profile</li>
        <li>{bundle.imageryUrl ? "Greyscale CTX image, warm display tint" : "Imagery could not be loaded; plain surface"}</li>
      </ul>
      </details>
      {exag > 1 && <span className="terrain-plate terrain-exag-note">Relief drawn {exag}× taller than measured</span>}
      <button type="button" className="btn terrain-reset" onClick={() => ctxRef.current?.reset()}>Reset view</button>
    </div>
  );
}
