import { useCallback, useEffect, useState } from "react";

import { getMovies, recommend, wakeBackend } from "./api.js";
import Footer from "./components/Footer.jsx";
import MovieSection from "./components/MovieSection.jsx";
import PickBar from "./components/PickBar.jsx";
import ResultPage from "./components/ResultPage.jsx";
import StatusMessage from "./components/StatusMessage.jsx";
import { isAtMax, togglePick } from "./picks.js";

const SECTIONS = [
  { key: "trending", title: "Trending this week" },
  { key: "popular", title: "Most popular" },
  { key: "all_time", title: "All-time favourites" },
];

export default function App() {
  const [step, setStep] = useState("home"); // "home" | "result"
  const [homeGrid, setHomeGrid] = useState(null);
  const [gridError, setGridError] = useState(null);
  const [picks, setPicks] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const loadHomeGrid = useCallback(async () => {
    setGridError(null);
    try {
      setHomeGrid(await getMovies());
    } catch (error) {
      setGridError(error.message);
    }
  }, []);

  useEffect(() => {
    wakeBackend();
    loadHomeGrid();
  }, [loadHomeGrid]);

  const toggle = (movieId) => {
    setSubmitError(null);
    setPicks((current) => togglePick(current, movieId));
  };

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
    setPicks([]);
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

          {gridError && <StatusMessage message={gridError} onRetry={loadHomeGrid} />}
          {!homeGrid && !gridError && (
            <StatusMessage message="Loading movies… The server may need a minute to wake up." />
          )}

          {homeGrid && (
            <>
              {SECTIONS.map(({ key, title }) => (
                <MovieSection
                  key={key}
                  title={title}
                  movies={homeGrid[key]}
                  picks={picks}
                  atMax={isAtMax(picks)}
                  onToggle={toggle}
                />
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
