"""Netflix-style picker rows (v2): recent hits first, then one row per genre, Japanese animation after Animation.

v1 showed "Trending this week" (TMDB trending in 2026 matched none of our <=2018 movies, so it fell back to
"Most popular"), "Most popular" (mostly 90s classics) and "All-time favourites" - so users could mostly only
pick old movies, and old picks give old recommendations.
"""

from collections.abc import Callable, Set
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from app.core.config import (
    BROWSE_GENRES,
    BROWSE_ROW_SIZE,
    GENRE_ROW_FROM_YEAR,
    MIN_ROW_SIZE,
    RECENT_FROM_YEAR,
)

JAPANESE = "ja"  # TMDB original_language code

MovieFilter = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True)
class MovieRow:
    key: str
    title: str
    movie_idxs: list[int]


def is_japanese_animation(movie: dict[str, Any]) -> bool:
    return "Animation" in movie["genres"] and movie["original_language"] == JAPANESE


def _in_genre_row(movie: dict[str, Any], genre: str) -> bool:
    if genre == "Animation" and is_japanese_animation(movie):
        return False  # they have their own row, right after this one; otherwise this row would take them all
    return genre in movie["genres"] and movie["year"] >= GENRE_ROW_FROM_YEAR


def _genre_filter(genre: str) -> MovieFilter:
    return lambda movie: _in_genre_row(movie, genre)


def _row_specs() -> list[tuple[str, str, MovieFilter, bool]]:
    """(key, title, which movies, newer_first). newer_first: 2010s movies before older ones, each by popularity."""
    specs: list[tuple[str, str, MovieFilter, bool]] = [
        ("recent", "Recent hits", lambda movie: movie["year"] >= RECENT_FROM_YEAR, False)
    ]
    anime: tuple[str, str, MovieFilter, bool] = (
        "japanese_animation",
        "Japanese animation",
        is_japanese_animation,
        True,
    )
    for genre in BROWSE_GENRES:
        # newer_first: pure popularity would favour the 2000s, as 2010s movies had less time to collect ratings.
        specs.append((genre.lower(), genre, _genre_filter(genre), True))
        if genre == "Animation":
            specs.append(anime)  # the two animation rows sit together
    return specs


def build_browse_rows(
    movies_by_idx: list[dict[str, Any]], rating_counts: npt.NDArray[np.float64], hidden_idxs: Set[int]
) -> list[MovieRow]:
    """Rows of popular matching movies; each movie appears once on the page (first row wins), hidden ones never."""
    by_popularity = np.argsort(-rating_counts, kind="stable").tolist()
    # Stable sort, so each group keeps its popularity order.
    newer_first = sorted(by_popularity, key=lambda idx: movies_by_idx[idx]["year"] < RECENT_FROM_YEAR)
    shown: set[int] = set(hidden_idxs)  # treated as already shown, so no row takes them
    rows: list[MovieRow] = []

    for key, title, keep, is_newer_first in _row_specs():
        order = newer_first if is_newer_first else by_popularity
        idxs = [idx for idx in order if idx not in shown and keep(movies_by_idx[idx])][:BROWSE_ROW_SIZE]
        if len(idxs) >= MIN_ROW_SIZE:  # a row of 1-3 posters looks broken
            rows.append(MovieRow(key, title, idxs))
            shown.update(idxs)
    return rows
