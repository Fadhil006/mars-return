import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { layerCanvas } from "../map/layers";
import { extentM, returnRetraces } from "../mission/geo";
import type { Mission } from "../mission/state";
import type { XY } from "../mission/types";
import { heightfield, surfacePoint } from "./scene";
import "./terrain.css";

const ROUTE = 0x3dd6e8, HYPOTHETICAL = 0xc9a0ff, WHITE = 0xffffff, BACKGROUND = 0x14171a;
const LIFT_M = 3; // display-only offset that keeps lines from flickering against the surface

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
  material: THREE.MeshLambertMaterial;
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
  const [lost, setLost] = useState(false);
  const usable = !!bundle?.elevation && webglAvailable() && !lost;

  const point = (xy: XY, lift = LIFT_M) => {
    const p = ctxRef.current && surfacePoint(bundle!, xy, ctxRef.current.origin, lift);
    return p ? new THREE.Vector3(...p) : null;
  };
  // shortcut: THREE.Line draws 1 px lines with no dark casing, switch to Line2 fat lines if routes read poorly over the imagery.
  const addLine = (group: THREE.Group, path: XY[] | null | undefined, color: number, opacity = 1, dashed = false) => {
    const points = (path ?? []).map((xy) => point(xy)).filter((p) => p !== null);
    if (points.length < 2) return;
    const options = { color, opacity, transparent: opacity < 1 };
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),
      dashed ? new THREE.LineDashedMaterial({ ...options, dashSize: 40, gapSize: 30 }) : new THREE.LineBasicMaterial(options));
    line.computeLineDistances();
    group.add(line);
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
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    } catch {
      setLost(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(BACKGROUND);
    // One neutral light pair; nothing decorative that could be read as terrain data.
    scene.add(new THREE.AmbientLight(WHITE, 1.6));
    const sun = new THREE.DirectionalLight(WHITE, 2.2);
    sun.position.set(-1, 2, -1); // from the north-west, above
    scene.add(sun);

    const field = heightfield(bundle);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(field.positions, 3));
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(field.uvs, 2));
    geometry.setIndex(field.indices);
    geometry.computeVertexNormals();
    const material = new THREE.MeshLambertMaterial({ color: 0x8a8580, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    scene.add(new THREE.Mesh(geometry, material));

    const groups = { route: new THREE.Group(), marks: new THREE.Group(), corridor: new THREE.Group(), ret: new THREE.Group() };
    scene.add(...Object.values(groups));

    const manifest = bundle.region.manifest, { w, h } = extentM(manifest), span = Math.max(w, h);
    geometry.computeBoundingBox();
    const centre = new THREE.Vector3(manifest.originXY[0] + w / 2, geometry.boundingBox!.max.y / 2, -(manifest.originXY[1] + h / 2));
    const camera = new THREE.PerspectiveCamera(45, 1, span / 500, span * 10);
    const controls = new OrbitControls(camera, canvas); // no damping: every camera move is immediate
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minDistance = span / 20;
    controls.maxDistance = span * 3;
    const render = () => {
      renderer.render(scene, camera);
      if (northRef.current) northRef.current.style.transform = `rotate(${controls.getAzimuthalAngle()}rad)`;
    };
    const reset = () => {
      controls.target.copy(centre);
      camera.position.set(centre.x + span * 0.55, centre.y + span * 0.6, centre.z + span * 0.55); // from the south-east, looking north-west
      controls.update();
      render();
    };
    controls.addEventListener("change", render);
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

    ctxRef.current = { renderer, scene, camera, controls, material, groups, origin: field.origin, render, reset };
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
      if (image) g.drawImage(image, 0, 0, canvas.width, canvas.height);
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
    ctx.render();
  }, [bundle, usable, m.assessment, state.freshness, state.rehearsing, m.posIndex]);

  // Base, science stops and the rover traverse.
  useEffect(() => {
    const ctx = ctxRef.current;
    if (!ctx || !bundle) return;
    const group = ctx.groups.marks;
    clear(group);
    if (m.baseXY) addMark(group, new THREE.BoxGeometry(28, 28, 28), m.baseXY, WHITE, 14);
    if (layers.stops) for (const stop of bundle.region.scienceStops) {
      addMark(group, new THREE.SphereGeometry(13, 16, 12), stop.positionXY, WHITE, 13);
      if (stop.id === state.inputs.targetId) {
        addMark(group, new THREE.RingGeometry(24, 32, 32).rotateX(-Math.PI / 2), stop.positionXY, ROUTE, 5, true);
      }
    }
    if (layers.traverse) addLine(group, bundle.traverse?.pathXY, 0xb3bcc4, 0.8);
    ctx.render();
  }, [bundle, usable, layers.stops, layers.traverse, state.inputs.targetId, m.baseXY]);

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
  }, [bundle, usable, corridorKey]);

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
  }, [bundle, usable, ret]);

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
        aria-label="3D terrain from elevation data at true vertical scale, with the same route and markers as the 2D map. Arrow keys orbit, plus and minus zoom." />
      <div className="terrain-info">
        <span className="terrain-plate">Vertical scale 1×</span>
        <span className="terrain-plate terrain-north"><span ref={northRef} aria-hidden="true">↑</span> N</span>
      </div>
      <ul className="terrain-legend terrain-plate" aria-label="3D marks">
        <li>■ Base · Hypothetical</li>
        {layers.stops && <li>● Science stop</li>}
        {m.points.length > 0 && <li><span className="terrain-route">━</span> Outbound <span className="terrain-route">┅</span> Return{state.freshness !== "current" && " · Outdated"}</li>}
        {state.rehearsing && <li><span className="terrain-route">◆</span> Current position</li>}
        {(m.corridor || ret) && <li><span className="terrain-hyp">━</span> Hypothetical scenario</li>}
        <li>Gaps: no elevation data</li>
      </ul>
      <button type="button" className="btn terrain-reset" onClick={() => ctxRef.current?.reset()}>Reset view</button>
    </div>
  );
}
