import type { Mission } from "../mission/state";

export function MissionMap({ m }: { m: Mission }) {
  return <div data-stub="MissionMap">{m.state.freshness}</div>;
}
