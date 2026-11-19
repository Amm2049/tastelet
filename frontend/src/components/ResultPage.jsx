import MovieCard from "./MovieCard.jsx";

export default function ResultPage({ result, onStartOver }) {
  return (
    <main className="result">
      <p className="eyebrow">Your taste persona</p>
      <h1 className="persona">{result.persona}</h1>
      <p className="description">{result.description}</p>
      <p className="genre-sentence">{result.genre_sentence}</p>

      <h2>Recommended for you</h2>
      <div className="poster-grid">
        {result.recommendations.map((movie) => (
          <MovieCard key={movie.id} movie={movie} matchScore={movie.score} />
        ))}
      </div>

      <button type="button" className="primary start-over" onClick={onStartOver}>
        Start over
      </button>
    </main>
  );
}
