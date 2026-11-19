import { useState } from "react";

export default function MovieCard({ movie, selected = false, disabled = false, matchScore, onToggle }) {
  const [posterFailed, setPosterFailed] = useState(false);
  const poster = posterFailed ? (
    <div className="poster poster-fallback" aria-hidden="true">
      {movie.title}
    </div>
  ) : (
    <img
      className="poster"
      src={movie.poster}
      alt={`Poster of ${movie.title}`}
      loading="lazy"
      onError={() => setPosterFailed(true)}
    />
  );
  const caption = (
    <span className="movie-caption">
      <span className="movie-title">{movie.title}</span>
      {movie.year && <span className="movie-year">{movie.year}</span>}
      {matchScore !== undefined && <span className="match">{matchScore}% match</span>}
    </span>
  );

  if (!onToggle) {
    return (
      <div className="movie-card">
        {poster}
        {caption}
      </div>
    );
  }
  return (
    <button
      type="button"
      className={`movie-card selectable${selected ? " selected" : ""}`}
      aria-pressed={selected}
      disabled={disabled}
      onClick={() => onToggle(movie.id)}
    >
      {poster}
      {selected && (
        <span className="check" aria-hidden="true">
          ✓
        </span>
      )}
      {caption}
    </button>
  );
}
