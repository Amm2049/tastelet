from collections.abc import Iterator

import pytest
import torch
from fastapi.testclient import TestClient

from app.core.config import BROWSE_GENRES
from app.main import create_app

ANIMATION_PICKS = [1, 364, 588, 6377, 4886]
TOY_STORY_2 = 3114


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:  # `with` runs the startup lifespan
        yield test_client


def test_startup_limits_torch_to_one_thread(client: TestClient) -> None:
    # Many threads on a shared free-tier CPU made /recommend take up to 18 s (issue #22).
    assert torch.get_num_threads() == 1


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_movies_returns_recent_hits_then_genres_with_japanese_animation_after_animation(client: TestClient) -> None:
    rows = client.get("/movies").json()["rows"]
    titles = [row["title"] for row in rows]

    assert titles[0] == "Recent hits"
    assert all(movie["year"] >= 2010 for movie in rows[0]["movies"])
    assert [title for title in titles[1:] if title != "Japanese animation"] == BROWSE_GENRES
    anime_position = titles.index("Japanese animation")
    assert titles[anime_position - 1] == "Animation"
    assert any(movie["title"].startswith("Spirited Away") for movie in rows[anime_position]["movies"])
    for row in rows:
        assert len(row["movies"]) >= 4
        assert all(movie["poster"].startswith("https://") for movie in row["movies"])
    assert set(rows[0]["movies"][0]) == {"id", "title", "year", "genres", "poster"}


def test_movies_shows_each_movie_once(client: TestClient) -> None:
    rows = client.get("/movies").json()["rows"]

    ids = [movie["id"] for row in rows for movie in row["movies"]]
    assert len(ids) == len(set(ids))


def test_search_finds_titles_with_the_article_moved_back(client: TestClient) -> None:
    movies = client.get("/movies/search", params={"q": "dark knight"}).json()["movies"]

    assert movies[0]["title"] == "The Dark Knight"


def test_search_with_a_too_short_query_returns_nothing(client: TestClient) -> None:
    response = client.get("/movies/search", params={"q": "x"})

    assert response.status_code == 200
    assert response.json() == {"movies": []}


def test_recommend_returns_persona_sentence_and_twenty_movies(client: TestClient) -> None:
    response = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS})

    body = response.json()
    assert response.status_code == 200
    assert body["persona"] == "The Dreamer"
    assert body["description"]
    assert body["genre_sentence"].startswith("You gravitate toward")
    assert len(body["recommendations"]) == 20
    assert not {movie["id"] for movie in body["recommendations"]} & set(ANIMATION_PICKS)
    assert set(body["recommendations"][0]) == {"id", "title", "year", "genres", "overview", "poster", "score"}


def test_recommend_adds_captioned_genre_rows_without_repeats(client: TestClient) -> None:
    body = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS}).json()

    rows = body["genre_rows"]
    assert rows[0]["title"] == "Because you love Adventure"  # the picks' most common genre
    assert all(row["caption"] for row in rows)
    shown = [movie["id"] for movie in body["recommendations"]] + [m["id"] for row in rows for m in row["movies"]]
    assert len(shown) == len(set(shown))
    assert not set(shown) & set(ANIMATION_PICKS)
    franchise_ids = {movie["id"] for movie in body["franchise_row"]["movies"]}
    assert not franchise_ids & {m["id"] for row in rows for m in row["movies"]}


def test_recommend_adds_a_franchise_row_for_toy_story(client: TestClient) -> None:
    body = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS}).json()  # includes Toy Story

    row = body["franchise_row"]
    assert row["title"] == "More from your franchises"
    assert "Toy Story" in row["caption"]
    assert TOY_STORY_2 in [movie["id"] for movie in row["movies"]]
    assert not {movie["id"] for movie in row["movies"]} & set(ANIMATION_PICKS)


def test_recommend_has_no_franchise_row_without_franchise_picks(client: TestClient) -> None:
    standalone_movies = [318, 2959, 296, 356, 50]  # Shawshank, Fight Club, Pulp Fiction, Forrest Gump, Usual Suspects
    body = client.post("/recommend", json={"movie_ids": standalone_movies}).json()

    assert body["franchise_row"] is None


def test_recommend_is_deterministic(client: TestClient) -> None:
    first = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS}).json()
    second = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS[::-1]}).json()

    assert first == second


@pytest.mark.parametrize(
    ("movie_ids", "message"),
    [
        (ANIMATION_PICKS[:4], "Pick between 5 and 10 movies."),
        (list(range(1, 12)), "Pick between 5 and 10 movies."),
        ([1, 1, 364, 588, 6377], "Each movie can only be picked once."),
        ([*ANIMATION_PICKS[:4], 999_999_999], "Unknown movie id(s): 999999999."),
    ],
)
def test_recommend_rejects_bad_picks_with_a_plain_message(
    client: TestClient, movie_ids: list[int], message: str
) -> None:
    response = client.post("/recommend", json={"movie_ids": movie_ids})

    assert response.status_code == 422
    assert response.json() == {"detail": message}


def test_recommend_rejects_a_malformed_body(client: TestClient) -> None:
    response = client.post("/recommend", json={"movies": ANIMATION_PICKS})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_cors_allows_the_local_frontend(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
