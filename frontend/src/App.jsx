import { useCallback, useEffect, useState } from "react";

import { getMovies, recommend, wakeBackend } from "./api.js";
import Footer from "./components/Footer.jsx";
import MovieCard from "./components/MovieCard.jsx";
import MovieRow from "./components/MovieRow.jsx";
import PickBar from "./components/PickBar.jsx";
import ResultPage from "./components/ResultPage.jsx";
import SearchResults from "./components/SearchResults.jsx";
import StatusMessage from "./components/StatusMessage.jsx";
import { isAtMax, togglePick } from "./picks.js";
import { useMovieSearch } from "./useMovieSearch.js";

export default function App() {
  const [step, setStep] = useState("home"); // "home" | "result"
  const [homeRows, setHomeRows] = useState(null);
  const [rowsError, setRowsError] = useState(null);
  // Whole movie objects, not just ids, so "Your picks" can show movies found by search.
  const [pickedMovies, setPickedMovies] = useState([]);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const search = useMovieSearch(query);
  const picks = pickedMovies.map((movie) => movie.id);

  const loadHomeRows = useCallback(async () => {
    setRowsError(null);
    try {
      setHomeRows((await getMovies()).rows);
    } catch (error) {
      setRowsError(error.message);
    }
  }, []);

  useEffect(() => {
    wakeBackend();
    loadHomeRows();
  }, [loadHomeRows]);

  const toggle = (movie) => {
    setSubmitError(null);
    setPickedMovies((current) => {
      const nextIds = togglePick(
        current.map((picked) => picked.id),
        movie.id,
      );
      return nextIds.map((id) => current.find((picked) => picked.id === id) ?? movie);
    });
  };

  const pickCards = (movies) =>
    movies.map((movie) => {
      const selected = picks.includes(movie.id);
      return (
        <MovieCard
          key={movie.id}
          movie={movie}
          selected={selected}
          disabled={isAtMax(picks) && !selected}
          onToggle={toggle}
        />
      );
    });

  const submitPicks = async () => {
    setSubmitError(null);
    setLoading(true);
    try {
      setResult(await recommend(picks));
      setStep("result");
      window.scrollTo({ top: 0 });
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const startOver = () => {
    setPickedMovies([]);
    setQuery("");
    setResult(null);
    setSubmitError(null);
    setStep("home");
    window.scrollTo({ top: 0 });
  };

  return (
    <div className="app">
      <header className="header">
        <span className="logo">Tastelet</span>
      </header>

      {step === "result" && result ? (
        <ResultPage result={result} onStartOver={startOver} />
      ) : (
        <main className="home">
          <h1>Pick movies you love</h1>
          <p className="intro">Choose 5 to 10 favourites and get your taste persona and recommendations.</p>

          {rowsError && <StatusMessage message={rowsError} onRetry={loadHomeRows} />}
          {!homeRows && !rowsError && (
            <StatusMessage message="Loading movies… The server may need a minute to wake up." />
          )}

          {homeRows && (
            <>
              <input
                className="search"
                type="search"
                placeholder="Search for a movie…"
                aria-label="Search for a movie"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <SearchResults search={search} renderCards={pickCards} />
              {pickedMovies.length > 0 && <MovieRow title="Your picks">{pickCards(pickedMovies)}</MovieRow>}
              {homeRows.map((row) => (
                <MovieRow key={row.key} title={row.title}>
                  {pickCards(row.movies)}
                </MovieRow>
              ))}
              <PickBar picks={picks} loading={loading} error={submitError} onSubmit={submitPicks} />
            </>
          )}
        </main>
      )}

      <Footer />
    </div>
  );
}
