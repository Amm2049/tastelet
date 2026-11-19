import MovieCard from "./MovieCard.jsx";

export default function MovieSection({ title, movies, picks, atMax, onToggle }) {
  return (
    <section className="movie-section" aria-label={title}>
      <h2>{title}</h2>
      <div className="poster-grid">
        {movies.map((movie) => {
          const selected = picks.includes(movie.id);
          return (
            <MovieCard
              key={movie.id}
              movie={movie}
              selected={selected}
              disabled={atMax && !selected}
              onToggle={onToggle}
            />
          );
        })}
      </div>
    </section>
  );
}
