import type { Mission } from "./state";

export function RehearsalStrip({ m }: { m: Mission }) {
  return <div data-stub="RehearsalStrip">{m.state.freshness}</div>;
}
