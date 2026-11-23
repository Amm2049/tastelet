import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App.jsx";

const movie = (id) => ({
  id,
  title: `Movie ${id}`,
  year: 2000 + id,
  genres: ["Drama"],
  poster: `https://img/${id}.jpg`,
});
const HOME_ROWS = {
  rows: [
    { key: "recent", title: "Recent hits", movies: [1, 2, 3, 4].map(movie) },
    { key: "comedy", title: "Comedies", movies: [5, 6, 7, 8].map(movie) },
    { key: "all_time", title: "All-time favourites", movies: [9, 10, 11, 12].map(movie) },
  ],
};
const recommended = (id, score) => ({ ...movie(id), overview: `About movie ${id}.`, score });
const RESULT = {
  persona: "The Dreamer",
  description: "Animation and fantasy worlds.",
  genre_sentence: "You gravitate toward Animation and Fantasy, especially films from the 1990s.",
  recommendations: [recommended(20, 99), recommended(21, 90)],
  franchise_row: {
    title: "More from your franchises",
    caption: "Because you picked Toy Story.",
    movies: [recommended(23, 70)],
  },
  genre_rows: [
    {
      title: "Because you love Animation",
      caption: "Drawn to your taste, frame by frame.",
      movies: [recommended(22, 80)],
    },
  ],
};

const jsonResponse = (body, status = 200) => Promise.resolve({ ok: status < 400, status, json: async () => body });

function mockApi({ recommendResponse = () => jsonResponse(RESULT) } = {}) {
  const fetchMock = vi.fn((url, options) => {
    if (url.endsWith("/health")) return jsonResponse({ status: "ok" });
    if (url.endsWith("/movies")) return jsonResponse(HOME_ROWS);
    if (url.includes("/movies/search?q=")) {
      const query = decodeURIComponent(url.split("q=")[1]);
      return jsonResponse({ movies: query === "space" ? [movie(30)] : [] });
    }
    if (url.endsWith("/recommend")) return recommendResponse(JSON.parse(options.body));
    throw new Error(`unexpected ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const row = (name) => screen.getByRole("region", { name });

async function pickMovies(user, ids) {
  for (const id of ids) {
    const rowName = HOME_ROWS.rows.find((r) => r.movies.some((m) => m.id === id)).title;
    await screen.findByRole("region", { name: rowName });
    await user.click(within(row(rowName)).getByRole("button", { name: new RegExp(`Movie ${id} `) }));
  }
}

beforeEach(() => {
  window.scrollTo = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows the picker rows from the API and wakes the backend", async () => {
    const fetchMock = mockApi();
    render(<App />);

    for (const { title } of HOME_ROWS.rows) {
      expect(await screen.findByRole("region", { name: title })).toBeInTheDocument();
    }
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/health$/));
  });

  it("keeps the submit button disabled below 5 picks and lists the picks in their own row", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 3, 4]);

    expect(screen.getByText("4/5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "See my results" })).toBeDisabled();
    expect(within(row("Your picks")).getAllByRole("button", { pressed: true })).toHaveLength(4);
  });

  it("disables unpicked movies at 10 picks", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);

    expect(screen.getByText("10/10")).toBeInTheDocument();
    const allTime = within(row("All-time favourites"));
    expect(allTime.getByRole("button", { name: /Movie 11 / })).toBeDisabled();
    expect(allTime.getByRole("button", { name: /Movie 10 / })).toBeEnabled();
  });

  it("finds a movie by search and lets the user pick it", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByRole("searchbox", { name: "Search for a movie" }), "space");
    const results = await screen.findByRole("region", { name: "Results for “space”" });
    await user.click(within(results).getByRole("button", { name: /Movie 30 / }));

    expect(within(row("Your picks")).getByRole("button", { name: /Movie 30 / })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("says so when a search finds nothing", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await user.type(await screen.findByRole("searchbox", { name: "Search for a movie" }), "zzz");

    expect(await screen.findByText("No movies match “zzz”.")).toBeInTheDocument();
  });

  it("sends the picks and shows persona, sentence, hero and captioned rows; Start over resets", async () => {
    const recommendResponse = vi.fn(() => jsonResponse(RESULT));
    mockApi({ recommendResponse });
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 5, 9, 12]);
    await user.click(screen.getByRole("button", { name: "See my results" }));

    expect(await screen.findByRole("heading", { name: "The Dreamer" })).toBeInTheDocument();
    expect(recommendResponse).toHaveBeenCalledWith({ movie_ids: [1, 2, 5, 9, 12] });
    expect(screen.getByText(RESULT.genre_sentence)).toBeInTheDocument();
    const hero = screen.getByRole("region", { name: "Your top match" });
    expect(within(hero).getByRole("heading", { name: "Movie 20" })).toBeInTheDocument();
    expect(within(hero).getByText("99% match")).toBeInTheDocument();
    expect(within(row("Top picks for you")).getByText("90% match")).toBeInTheDocument();
    expect(
      within(row("Because you love Animation")).getByText("Drawn to your taste, frame by frame."),
    ).toBeInTheDocument();
    const franchise = within(row("More from your franchises"));
    expect(franchise.getByText("Because you picked Toy Story.")).toBeInTheDocument();
    expect(franchise.getByText("70% match")).toBeInTheDocument();
    const rowTitles = screen.getAllByRole("region").map((region) => region.getAttribute("aria-label"));
    expect(rowTitles.indexOf("More from your franchises")).toBe(rowTitles.indexOf("Top picks for you") + 1);

    await user.click(screen.getByRole("button", { name: "Start over" }));

    expect(await screen.findByText("0/5")).toBeInTheDocument();
    expect(within(row("Recent hits")).getByRole("button", { name: /Movie 1 / })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("shows the server's plain error message and lets the user try again", async () => {
    let calls = 0;
    mockApi({
      recommendResponse: () =>
        ++calls === 1 ? jsonResponse({ detail: "Unknown movie id(s): 12." }, 422) : jsonResponse(RESULT),
    });
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 5, 9, 12]);
    await user.click(screen.getByRole("button", { name: "See my results" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unknown movie id(s): 12.");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "The Dreamer" })).toBeInTheDocument();
  });

  it("shows a retry message when the movies cannot load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("network down"))),
    );
    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Can't reach the server");
    expect(within(alert).getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("shows a placeholder when a poster fails to load", async () => {
    mockApi();
    render(<App />);

    const poster = await screen.findByAltText("Poster of Movie 1");
    poster.dispatchEvent(new Event("error"));

    await waitFor(() => expect(screen.queryByAltText("Poster of Movie 1")).not.toBeInTheDocument());
  });
});
