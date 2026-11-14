import type { Mission } from "./state";

export function MissionControls({ m }: { m: Mission }) {
  return <div data-stub="MissionControls">{m.state.freshness}</div>;
}
