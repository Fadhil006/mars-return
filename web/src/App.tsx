import { useMission } from "./mission/state";

export function App() {
  const m = useMission();
  return <pre>{m.state.regionStatus}</pre>;
}
