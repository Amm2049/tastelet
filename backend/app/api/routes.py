"""HTTP routes. Thin: validate (Pydantic), call a service, shape the response."""

from typing import Any

from fastapi import APIRouter, Request

from app.repositories.artifacts import Artifacts
from app.schemas.api import (
    HealthResponse,
    HomeRowsResponse,
    MovieCard,
    MovieRowResponse,
    RecommendedMovie,
    RecommendRequest,
    RecommendResponse,
    ResultRowResponse,
    SearchResponse,
)
from app.services.browse import build_browse_rows
from app.services.genre_sentence import genre_sentence
from app.services.recommender import Recommendation, recommend_for_picks
from app.services.result_rows import ResultRow, build_franchise_row, build_genre_rows
from app.services.search import search_movies
from app.services.titles import display_title

router = APIRouter()


def _artifacts(request: Request) -> Artifacts:
    artifacts: Artifacts = request.app.state.artifacts
    return artifacts


def _movie_card(movie: dict[str, Any]) -> MovieCard:
    return MovieCard(
        id=movie["id"],
        title=display_title(movie["title"]),
        year=movie["year"],
        genres=movie["genres"],
        poster=movie["poster"],
    )


def _recommended_movie(recommendation: Recommendation, artifacts: Artifacts) -> RecommendedMovie:
    movie = artifacts.movies_by_idx[recommendation.movie_idx]
    return RecommendedMovie(
        **_movie_card(movie).model_dump(), overview=movie["overview"], score=recommendation.match_percent
    )


def _row_response(row: ResultRow, artifacts: Artifacts) -> ResultRowResponse:
    return ResultRowResponse(
        title=row.title, caption=row.caption, movies=[_recommended_movie(r, artifacts) for r in row.recommendations]
    )


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/movies")
def home_rows(request: Request) -> HomeRowsResponse:
    artifacts = _artifacts(request)
    rows = build_browse_rows(artifacts.movies_by_idx, artifacts.rating_counts)
    return HomeRowsResponse(
        rows=[
            MovieRowResponse(
                key=row.key,
                title=row.title,
                movies=[_movie_card(artifacts.movies_by_idx[idx]) for idx in row.movie_idxs],
            )
            for row in rows
        ]
    )


@router.get("/movies/search")
def search(request: Request, q: str = "") -> SearchResponse:
    artifacts = _artifacts(request)
    idxs = search_movies(q, artifacts.movies_by_idx, artifacts.rating_counts)
    return SearchResponse(movies=[_movie_card(artifacts.movies_by_idx[idx]) for idx in idxs])


# Plain `def` (not async): fold-in is CPU work, so FastAPI runs it in a worker thread
# instead of blocking every other request. Picks are never logged or stored (privacy rule).
@router.post("/recommend")
def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    artifacts = _artifacts(request)
    result = recommend_for_picks(artifacts, body.movie_ids)  # UnknownMovieError -> 422 in main.py
    persona = artifacts.personas[result.persona_id]
    picks = [artifacts.movie_idx_by_id[movie_id] for movie_id in body.movie_ids]
    picked_movies = [artifacts.movies_by_idx[idx] for idx in picks]
    franchise_row = build_franchise_row(
        picks, artifacts.movies_by_idx, artifacts.movie_idxs_by_collection, result.match_by_idx
    )
    franchise_idxs = {r.movie_idx for r in franchise_row.recommendations} if franchise_row else set()
    genre_rows = build_genre_rows(picked_movies, result.ranked, artifacts.movies_by_idx, shown_above=franchise_idxs)

    return RecommendResponse(
        persona=persona["name"],
        description=persona["description"],
        genre_sentence=genre_sentence(picked_movies),
        recommendations=[_recommended_movie(r, artifacts) for r in result.recommendations],
        franchise_row=_row_response(franchise_row, artifacts) if franchise_row else None,
        genre_rows=[_row_response(row, artifacts) for row in genre_rows],
    )
