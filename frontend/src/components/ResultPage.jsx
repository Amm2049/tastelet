import HeroMatch from "./HeroMatch.jsx";
import MovieCard from "./MovieCard.jsx";
import MovieRow from "./MovieRow.jsx";

const scoredCards = (movies) =>
  movies.map((movie) => <MovieCard key={movie.id} movie={movie} matchScore={movie.score} />);

const captionedRow = (row) => (
  <MovieRow key={row.title} title={row.title} caption={row.caption}>
    {scoredCards(row.movies)}
  </MovieRow>
);

export default function ResultPage({ result, onStartOver }) {
  const [topMatch, ...topPicks] = result.recommendations;

  return (
    <main className="result">
      {/* At the top, so trying new picks doesn't need a scroll past every row. */}
      <div className="result-top">
        <p className="eyebrow">Your taste persona</p>
        <button type="button" className="secondary" onClick={onStartOver}>
          Start over
        </button>
      </div>
      <h1 className="persona">{result.persona}</h1>
      <p className="description">{result.description}</p>
      <p className="genre-sentence">{result.genre_sentence}</p>

      <HeroMatch movie={topMatch} />

      <MovieRow title="Top picks for you" caption="Ranked by how closely they match your picks.">
        {scoredCards(topPicks)}
      </MovieRow>
      {result.franchise_row && captionedRow(result.franchise_row)}
      {result.genre_rows.map(captionedRow)}
    </main>
  );
}
