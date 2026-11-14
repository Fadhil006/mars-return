import type { Mission } from "../mission/state";

/** False when this browser cannot create a WebGL context; the 3D toggle is then disabled. */
export function webglAvailable(): boolean {
  return false; // stub
}

export function TerrainView({ m }: { m: Mission }) {
  return <div data-stub="TerrainView">{m.state.freshness}</div>;
}
