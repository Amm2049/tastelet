from typing import Any

import pytest

from app.repositories.artifacts import UNKNOWN_YEAR, Artifacts, is_showable

POSTER = "https://image.tmdb.org/t/p/w342/poster.jpg"


@pytest.mark.parametrize(
    ("movie", "expected"),
    [
        ({"poster": POSTER, "year": 2019}, True),
        ({"poster": None, "year": 2019}, False),
        ({"poster": "", "year": 2019}, False),
        ({"poster": POSTER, "year": None}, False),
    ],
)
def test_only_movies_with_a_poster_and_a_year_are_showable(movie: dict[str, Any], expected: bool) -> None:
    assert is_showable(movie) is expected


def test_hidden_movies_get_a_placeholder_year_so_every_year_is_an_int(artifacts: Artifacts) -> None:
    hidden_years = {artifacts.movies_by_idx[idx]["year"] for idx in artifacts.hidden_idxs}

    assert all(isinstance(movie["year"], int) for movie in artifacts.movies_by_idx)
    assert UNKNOWN_YEAR in hidden_years  # the v3 catalog has movies without a year


def test_franchises_only_list_shown_movies(artifacts: Artifacts) -> None:
    in_franchises = {idx for idxs in artifacts.movie_idxs_by_collection.values() for idx in idxs}

    assert in_franchises
    assert not in_franchises & artifacts.hidden_idxs


def test_scaled_popularity_runs_from_0_to_1_in_rating_count_order(artifacts: Artifacts) -> None:
    most_rated = int(artifacts.rating_counts.argmax())

    assert artifacts.scaled_popularity.min() >= 0.0
    assert artifacts.scaled_popularity[most_rated] == 1.0
    order = artifacts.rating_counts.argsort(kind="stable")
    assert (artifacts.scaled_popularity[order][1:] >= artifacts.scaled_popularity[order][:-1]).all()
