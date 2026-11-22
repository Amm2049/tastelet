"""Request and response shapes of the API (spec: "API endpoints")."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import MAX_PICKS, MIN_PICKS


class MovieCard(BaseModel):
    id: int
    title: str
    year: int
    genres: list[str]
    poster: str


class MovieRowResponse(BaseModel):
    key: str
    title: str
    movies: list[MovieCard]


class HomeRowsResponse(BaseModel):
    rows: list[MovieRowResponse]


class SearchResponse(BaseModel):
    movies: list[MovieCard]


class RecommendRequest(BaseModel):
    movie_ids: list[int] = Field(min_length=MIN_PICKS, max_length=MAX_PICKS)

    @field_validator("movie_ids")
    @classmethod
    def picks_are_unique(cls, movie_ids: list[int]) -> list[int]:
        # Otherwise one movie picked 5 times would count as 5 picks.
        if len(set(movie_ids)) != len(movie_ids):
            raise ValueError("each movie can only be picked once")
        return movie_ids


class RecommendedMovie(BaseModel):
    id: int
    title: str
    year: int
    genres: list[str]
    overview: str
    poster: str
    score: int = Field(description="Match score in percent (0-100)")


class ResultRowResponse(BaseModel):
    title: str
    caption: str
    movies: list[RecommendedMovie]


class RecommendResponse(BaseModel):
    persona: str
    description: str
    genre_sentence: str
    recommendations: list[RecommendedMovie] = Field(description="Best first; the first one is the hero")
    franchise_row: ResultRowResponse | None = Field(description="Other movies of the picks' franchises, if any")
    genre_rows: list[ResultRowResponse]


class HealthResponse(BaseModel):
    status: Literal["ok"]
