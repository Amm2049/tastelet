from typing import Any

import numpy as np
import pytest

from app.services.search import search_movies
from app.services.titles import display_title, search_key


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Dark Knight, The", "The Dark Knight"),
        ("Few Good Men, A", "A Few Good Men"),
        (
            "City of Lost Children, The (Cité des enfants perdus, La)",
            "The City of Lost Children (Cité des enfants perdus, La)",
        ),
        ("Toy Story", "Toy Story"),
        ("Crouching Tiger, Hidden Dragon", "Crouching Tiger, Hidden Dragon"),  # comma, but no article
    ],
)
def test_display_title_moves_the_article_back_to_the_front(title: str, expected: str) -> None:
    assert display_title(title) == expected


def test_search_key_ignores_case_and_punctuation() -> None:
    assert search_key("Spider-Man: Homecoming") == "spider man homecoming"


MOVIES: list[dict[str, Any]] = [
    {"title": "Toys"},
    {"title": "Toy Story"},
    {"title": "Babes in Toyland"},
    {"title": "Toy Story 2"},
]
RATING_COUNTS = np.array([5.0, 200.0, 50.0, 100.0])


def test_search_puts_title_prefix_matches_first_then_the_most_rated() -> None:
    assert search_movies("toy", MOVIES, RATING_COUNTS) == [1, 3, 0, 2]


@pytest.mark.parametrize("query", ["", " ", "t", "-", "zzz"])
def test_search_returns_nothing_for_short_or_unmatched_queries(query: str) -> None:
    assert search_movies(query, MOVIES, RATING_COUNTS) == []


def test_search_ignores_text_past_the_length_cap() -> None:
    assert search_movies("toy" + " " * 200 + "zzz", MOVIES, RATING_COUNTS) == [1, 3, 0, 2]
