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


class HomeGridResponse(BaseModel):
    trending: list[MovieCard]
    popular: list[MovieCard]
    all_time: list[MovieCard]


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
    poster: str
    score: int = Field(description="Match score in percent (0-100)")


class RecommendResponse(BaseModel):
    persona: str
    description: str
    genre_sentence: str
    recommendations: list[RecommendedMovie]


class HealthResponse(BaseModel):
    status: Literal["ok"]
