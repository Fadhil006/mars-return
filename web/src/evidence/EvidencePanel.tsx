import type { Mission } from "../mission/state";

export function EvidencePanel({ m }: { m: Mission }) {
  return <div data-stub="EvidencePanel">{m.state.freshness}</div>;
}
