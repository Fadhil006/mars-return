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

/**
 * Hiking-style turnaround call from the two returned options, comparing returned margins only.
 * Null when there is nothing clear to say.
 */
export function turnaround(now: { status: string; marginMin?: number | null }, cont: { status: string; marginMin?: number | null }): string | null {
  if (now.status !== "ok" && cont.status !== "ok") return "Neither option fits the remaining time.";
  if (now.status === "ok" && cont.status !== "ok")
    return `Turn around now: continuing to the site ${cont.status === "over_budget" ? "no longer fits the remaining time" : "has no route"}. Returning now keeps ${hm(now.marginMin)} of margin.`;
  if (now.status === "ok" && cont.marginMin != null && now.marginMin != null)
    return `Continuing still fits, with ${hm(cont.marginMin)} of margin (${hm(now.marginMin - cont.marginMin)} less than returning now).`;
  return null;
}

/**
 * Galactic cosmic ray dose equivalent measured on the surface by Curiosity's RAD, Gale Crater, Aug 2012 to Jun 2013
 * (Hassler et al. 2014, Science, doi:10.1126/science.1244797; SwRI release, 9 Dec 2013). Source: data/sources/msl-rad.json.
 */
export const RAD_MSV_PER_DAY = 0.67;

/** Display-only estimate: the measured daily rate scaled to the planned minutes outside. Not a route value. */
export function doseMSv(minutes: number | null | undefined): number | null {
  return minutes == null ? null : (minutes / 1440) * RAD_MSV_PER_DAY;
}
