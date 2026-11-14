import type { Mission } from "../mission/state";

export function MissionReport({ m }: { m: Mission }) {
  return <div data-stub="MissionReport">{m.state.freshness}</div>;
}
