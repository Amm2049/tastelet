import { MAX_PICKS, MIN_PICKS, canSubmit, counterText, isAtMax } from "../picks.js";

function hintFor(picks, loading, error) {
  if (error) return error;
  if (loading) return "Finding your taste… The first request can take up to a minute while the server wakes up.";
  if (isAtMax(picks)) return `That's ${MAX_PICKS}, the maximum. Tap a pick to swap it.`;
  if (picks.length < MIN_PICKS) return `Pick at least ${MIN_PICKS} movies you love.`;
  return "Nice! Add more or see your results.";
}

export default function PickBar({ picks, loading, error, onSubmit }) {
  return (
    <div className="pick-bar">
      <div className="pick-status">
        <span className="counter" aria-label={`${picks.length} movies picked`}>
          {counterText(picks)}
        </span>
        <span className={`hint${error ? " hint-error" : ""}`} role={error ? "alert" : "status"}>
          {hintFor(picks, loading, error)}
        </span>
      </div>
      <button type="button" className="primary" disabled={!canSubmit(picks) || loading} onClick={onSubmit}>
        {loading ? "Working…" : error ? "Try again" : "See my results"}
      </button>
    </div>
  );
}
