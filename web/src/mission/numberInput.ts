/** Limits for a typed number. `above` is an exclusive lower bound (the service rejects speed 0). */
export interface NumberLimits { min?: number; above?: number; max?: number }

/**
 * Reads a typed number. Returns the value when it is a finite number within the limits, otherwise an error
 * sentence for the field. The text is never repaired: "-10" is an error, not 10 or 1010.
 */
export function checkNumber(text: string, { min, above, max }: NumberLimits = {}): { value: number } | { error: string } {
  const t = text.trim();
  const v = t === "" ? NaN : Number(t);
  if (!Number.isFinite(v)) return { error: "Enter a number." };
  if (above != null && v <= above) return { error: `Must be more than ${above}.` };
  if (min != null && v < min) return { error: `Must be ${min} or more.` };
  if (max != null && v > max) return { error: `Must be ${max} or less.` };
  return { value: v };
}
