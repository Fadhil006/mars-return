import type { Mission } from "./state";

export function RouteComparison({ m }: { m: Mission }) {
  return <div data-stub="RouteComparison">{m.state.freshness}</div>;
}
