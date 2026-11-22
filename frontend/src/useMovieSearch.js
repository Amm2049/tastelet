import { useEffect, useState } from "react";

import { searchMovies } from "./api.js";

export const MIN_SEARCH_LENGTH = 2; // same as the backend: shorter queries return nothing
const SEARCH_DELAY_MS = 300; // wait until the user pauses typing, instead of one request per key

// Search results for `query`, or { active: false } while the query is too short to search.
export function useMovieSearch(query) {
  const trimmed = query.trim();
  const [found, setFound] = useState({ query: "", movies: [], error: null });

  useEffect(() => {
    if (trimmed.length < MIN_SEARCH_LENGTH) return undefined;
    let cancelled = false; // a slow answer for an old query must not overwrite a newer one
    const timer = setTimeout(async () => {
      try {
        const { movies } = await searchMovies(trimmed);
        if (!cancelled) setFound({ query: trimmed, movies, error: null });
      } catch (error) {
        if (!cancelled) setFound({ query: trimmed, movies: [], error: error.message });
      }
    }, SEARCH_DELAY_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [trimmed]);

  if (trimmed.length < MIN_SEARCH_LENGTH) return { active: false };
  return { active: true, query: trimmed, ready: found.query === trimmed, movies: found.movies, error: found.error };
}
