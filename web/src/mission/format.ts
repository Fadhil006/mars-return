// Display rounding only; full-precision values stay in state.
export const DASH = "—";

export function num(value: number | null | undefined, digits = 0): string {
  return value == null ? DASH : value.toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** Signed difference between two returned values, e.g. "+33 m". Null when either side is missing. */
export function diff(a: number | null | undefined, b: number | null | undefined, digits = 0): string {
  if (a == null || b == null) return DASH;
  const d = b - a, text = num(Math.abs(d), digits);
  return Number(text.replace(/,/g, "")) === 0 ? "0" : `${d > 0 ? "+" : "−"}${text}`;
}

export const STATUS_TEXT: Record<string, string> = {
  ok: "Within budget", over_budget: "Over budget", no_path: "No route found",
  invalid_input: "Invalid input", data_unavailable: "Data unavailable",
};

/** Minutes as "5 h 10 m" (or "45 m"), rounded to the minute for display only. */
export function hm(min: number | null | undefined): string {
  if (min == null) return DASH;
  const t = Math.round(Math.abs(min)), h = Math.floor(t / 60), m = t % 60;
  return `${min < 0 && t ? "−" : ""}${h ? `${h} h ${String(m).padStart(2, "0")} m` : `${m} min`}`;
}
