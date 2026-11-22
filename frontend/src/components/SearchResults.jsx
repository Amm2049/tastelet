import MovieRow from "./MovieRow.jsx";

export default function SearchResults({ search, renderCards }) {
  if (!search.active) return null;
  if (!search.ready) return <p className="search-note">Searching…</p>;
  if (search.error) return <p className="search-note hint-error">{search.error}</p>;
  if (search.movies.length === 0) return <p className="search-note">No movies match “{search.query}”.</p>;
  return <MovieRow title={`Results for “${search.query}”`}>{renderCards(search.movies)}</MovieRow>;
}
