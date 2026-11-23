// The #1 recommendation as a big banner, like the featured title at the top of Netflix.
export default function HeroMatch({ movie }) {
  return (
    <section className="hero" aria-label="Your top match" style={{ "--hero-image": `url(${movie.poster})` }}>
      <img className="hero-poster" src={movie.poster} alt={`Poster of ${movie.title}`} />
      <div className="hero-info">
        <p className="eyebrow">Your #1 match</p>
        <h2 className="hero-title">{movie.title}</h2>
        <p className="hero-meta">
          <span className="match">{movie.score}% match</span> · {movie.year} · {movie.genres.join(", ")}
        </p>
        {movie.overview && <p className="hero-overview">{movie.overview}</p>}
      </div>
    </section>
  );
}
