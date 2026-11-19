export default function Footer() {
  return (
    <footer className="footer">
      <p>
        Ratings from{" "}
        <a href="https://grouplens.org/datasets/movielens/" target="_blank" rel="noreferrer">
          MovieLens
        </a>{" "}
        (GroupLens). Posters and data from{" "}
        <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
          TMDB
        </a>
        .
      </p>
      <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
    </footer>
  );
}
