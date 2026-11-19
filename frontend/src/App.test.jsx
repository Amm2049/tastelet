import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App.jsx";

const movie = (id) => ({
  id,
  title: `Movie ${id}`,
  year: 1990 + id,
  genres: ["Drama"],
  poster: `https://img/${id}.jpg`,
});
const HOME_GRID = {
  trending: [1, 2, 3, 4].map(movie),
  popular: [5, 6, 7, 8].map(movie),
  all_time: [9, 10, 11, 12].map(movie),
};
const RESULT = {
  persona: "The Dreamer",
  description: "Animation and fantasy worlds.",
  genre_sentence: "You gravitate toward Animation and Fantasy, especially films from the 1990s.",
  recommendations: [{ id: 20, title: "Shrek", poster: "https://img/20.jpg", score: 99 }],
};

const jsonResponse = (body, status = 200) => Promise.resolve({ ok: status < 400, status, json: async () => body });

function mockApi({ recommendResponse = () => jsonResponse(RESULT) } = {}) {
  const fetchMock = vi.fn((url, options) => {
    if (url.endsWith("/health")) return jsonResponse({ status: "ok" });
    if (url.endsWith("/movies")) return jsonResponse(HOME_GRID);
    if (url.endsWith("/recommend")) return recommendResponse(JSON.parse(options.body));
    throw new Error(`unexpected ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function pickMovies(user, ids) {
  for (const id of ids) await user.click(await screen.findByRole("button", { name: new RegExp(`Movie ${id} `) }));
}

beforeEach(() => {
  window.scrollTo = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows the three home sections and wakes the backend", async () => {
    const fetchMock = mockApi();
    render(<App />);

    for (const name of ["Trending this week", "Most popular", "All-time favourites"]) {
      expect(await screen.findByRole("region", { name })).toBeInTheDocument();
    }
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/health$/));
  });

  it("keeps the submit button disabled below 5 picks", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 3, 4]);

    expect(screen.getByText("4/5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "See my results" })).toBeDisabled();
  });

  it("disables unpicked movies at 10 picks", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);

    expect(screen.getByText("10/10")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Movie 11 / })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Movie 10 / })).toBeEnabled();
  });

  it("sends the picks and shows persona, sentence and recommendations; Start over resets", async () => {
    const recommendResponse = vi.fn(() => jsonResponse(RESULT));
    mockApi({ recommendResponse });
    const user = userEvent.setup();
    render(<App />);

    await pickMovies(user, [1, 2, 5, 9, 12]);
    await user.click(screen.getByRole("button", { name: "See my results" }));

    expect(await screen.findByRole("heading", { name: "The Dreamer" })).toBeInTheDocument();
    expect(recommendResponse).toHaveBeenCalledWith({ movie_ids: [1, 2, 5, 9, 12] });
    expect(screen.getByText(RESULT.genre_sentence)).toBeInTheDocument();
    expect(screen.getByText("99% match")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Start over" }));

    expect(await screen.findByText("0/5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Movie 1 / })).toHaveAttribute("aria-pressed", "false");
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
