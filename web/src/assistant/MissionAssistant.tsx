import type { Mission } from "../mission/state";

export function MissionAssistant({ m }: { m: Mission }) {
  return <div data-stub="MissionAssistant">{m.state.freshness}</div>;
}
