// Kept apart from TerrainView so the app can check for WebGL without downloading three.js.
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
