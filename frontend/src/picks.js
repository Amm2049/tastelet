// Pick rules (spec F2). The backend enforces the same limits; this only keeps the UI honest.
export const MIN_PICKS = 5;
export const MAX_PICKS = 10;

export function togglePick(picks, movieId) {
  if (picks.includes(movieId)) return picks.filter((id) => id !== movieId);
  if (picks.length >= MAX_PICKS) return picks;
  return [...picks, movieId];
}

export const canSubmit = (picks) => picks.length >= MIN_PICKS && picks.length <= MAX_PICKS;

export const isAtMax = (picks) => picks.length >= MAX_PICKS;

// "3/5" until the minimum is reached, then "7/10" so the user sees how many are left.
export const counterText = (picks) => `${picks.length}/${picks.length < MIN_PICKS ? MIN_PICKS : MAX_PICKS}`;
