from collections.abc import Iterator

import pytest
import torch
from fastapi.testclient import TestClient

from app.main import create_app

ANIMATION_PICKS = [1, 364, 588, 6377, 4886]


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


def test_movies_returns_three_home_lists_with_posters(client: TestClient) -> None:
    body = client.get("/movies").json()

    assert set(body) == {"trending", "popular", "all_time"}
    for movies in body.values():
        assert len(movies) >= 12
        assert all(movie["poster"].startswith("https://") for movie in movies)
        assert set(movies[0]) == {"id", "title", "year", "genres", "poster"}


def test_recommend_returns_persona_sentence_and_twenty_movies(client: TestClient) -> None:
    response = client.post("/recommend", json={"movie_ids": ANIMATION_PICKS})

    body = response.json()
    assert response.status_code == 200
    assert body["persona"] == "The Dreamer"
    assert body["description"]
    assert body["genre_sentence"].startswith("You gravitate toward")
    assert len(body["recommendations"]) == 20
    assert not {movie["id"] for movie in body["recommendations"]} & set(ANIMATION_PICKS)
    assert set(body["recommendations"][0]) == {"id", "title", "poster", "score"}


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
