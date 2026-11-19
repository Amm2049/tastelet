"""HTTP routes. Thin: validate (Pydantic), call a service, shape the response."""

from typing import Any

from fastapi import APIRouter, Request

from app.repositories.artifacts import Artifacts
from app.schemas.api import (
    HealthResponse,
    HomeGridResponse,
    MovieCard,
    RecommendedMovie,
    RecommendRequest,
    RecommendResponse,
)
from app.services.genre_sentence import genre_sentence
from app.services.recommender import recommend_for_picks

router = APIRouter()


def _artifacts(request: Request) -> Artifacts:
    artifacts: Artifacts = request.app.state.artifacts
    return artifacts


def _movie_card(movie: dict[str, Any]) -> MovieCard:
    return MovieCard(
        id=movie["id"], title=movie["title"], year=movie["year"], genres=movie["genres"], poster=movie["poster"]
    )


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/movies")
def home_grid(request: Request) -> HomeGridResponse:
    artifacts = _artifacts(request)

    def cards(list_name: str) -> list[MovieCard]:
        return [
            _movie_card(artifacts.movies_by_idx[artifacts.movie_idx_by_id[movie_id]])
            for movie_id in artifacts.home_lists[list_name]
        ]

    return HomeGridResponse(trending=cards("trending"), popular=cards("popular"), all_time=cards("all_time"))


# Plain `def` (not async): fold-in is CPU work, so FastAPI runs it in a worker thread
# instead of blocking every other request. Picks are never logged or stored (privacy rule).
@router.post("/recommend")
def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    artifacts = _artifacts(request)
    result = recommend_for_picks(artifacts, body.movie_ids)  # UnknownMovieError -> 422 in main.py
    persona = artifacts.personas[result.persona_id]
    picked_movies = [artifacts.movies_by_idx[artifacts.movie_idx_by_id[movie_id]] for movie_id in body.movie_ids]

    return RecommendResponse(
        persona=persona["name"],
        description=persona["description"],
        genre_sentence=genre_sentence(picked_movies),
        recommendations=[
            RecommendedMovie(
                id=movie["id"], title=movie["title"], poster=movie["poster"], score=recommendation.match_percent
            )
            for recommendation in result.recommendations
            for movie in [artifacts.movies_by_idx[recommendation.movie_idx]]
        ],
    )
