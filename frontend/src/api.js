const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error("Can't reach the server. Check your connection and try again.");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    // The backend sends one plain sentence in `detail` for bad input (422).
    throw new Error(typeof body?.detail === "string" ? body.detail : "Something went wrong. Please try again.");
  }
  return body;
}

export const getMovies = () => request("/movies");

export const searchMovies = (query) => request(`/movies/search?q=${encodeURIComponent(query)}`);

export const recommend = (movieIds) =>
  request("/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ movie_ids: movieIds }),
  });

// A free server sleeps when idle; pinging it on page load lets it wake while the user picks.
export const wakeBackend = () => fetch(`${API_URL}/health`).catch(() => {});
