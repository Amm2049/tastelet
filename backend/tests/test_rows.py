from typing import Any

import numpy as np

from app.core.config import BROWSE_ROW_SIZE, MIN_ROW_SIZE
from app.repositories.artifacts import Artifacts
from app.services.browse import build_browse_rows
from app.services.genre_sentence import NOT_A_GENRE
from app.services.recommender import Recommendation
from app.services.result_rows import GENRE_CAPTIONS, build_genre_rows


def movie(year: int, genres: list[str], language: str = "en") -> dict[str, Any]:
    return {"year": year, "genres": genres, "original_language": language}


def test_browse_rows_start_with_recent_hits_by_popularity() -> None:
    movies = [movie(2015, ["Drama"]) for _ in range(6)] + [movie(2005, ["Drama"]) for _ in range(6)]
    counts = np.arange(12, dtype=float)  # higher index = more ratings

    rows = build_browse_rows(movies, counts)

    assert rows[0].key == "recent"
    assert rows[0].movie_idxs == [5, 4, 3, 2, 1, 0]
    assert rows[1].key == "drama"  # only the 2000s dramas are left for it
    assert rows[1].movie_idxs == [11, 10, 9, 8, 7, 6]


def test_japanese_animation_gets_its_own_row_and_leaves_the_animation_row() -> None:
    western = [movie(2005, ["Animation"]) for _ in range(MIN_ROW_SIZE)]
    anime = [movie(2001, ["Animation", "Fantasy"], "ja") for _ in range(MIN_ROW_SIZE)]
    japanese_live_action = [movie(2003, ["Drama"], "ja")]
    movies = western + anime + japanese_live_action

    rows = {row.key: row.movie_idxs for row in build_browse_rows(movies, np.ones(len(movies)))}

    assert rows["animation"] == list(range(MIN_ROW_SIZE))
    assert rows["japanese_animation"] == list(range(MIN_ROW_SIZE, 2 * MIN_ROW_SIZE))


def test_japanese_animation_row_sits_right_after_animation() -> None:
    movies = [
        *[movie(1988, ["Animation"], "ja") for _ in range(MIN_ROW_SIZE)],  # 1988 is fine: no year limit here
        *[movie(2005, ["Comedy"]) for _ in range(MIN_ROW_SIZE)],
        *[movie(2005, ["Animation"]) for _ in range(MIN_ROW_SIZE)],
        *[movie(2005, ["Action"]) for _ in range(MIN_ROW_SIZE)],
    ]

    rows = build_browse_rows(movies, np.ones(len(movies)))

    assert [row.key for row in rows] == ["action", "animation", "japanese_animation", "comedy"]


def test_genre_rows_show_2010s_movies_before_more_rated_2000s_ones() -> None:
    popular_recent_dramas = [movie(2015, ["Drama"]) for _ in range(BROWSE_ROW_SIZE)]  # fill "Recent hits"
    comedies = [movie(2005, ["Comedy"]), movie(2012, ["Comedy"]), movie(2006, ["Comedy"]), movie(2016, ["Comedy"])]
    counts = np.array([1000.0] * BROWSE_ROW_SIZE + [300.0, 2.0, 200.0, 1.0])
    first_comedy = BROWSE_ROW_SIZE

    rows = build_browse_rows(popular_recent_dramas + comedies, counts)

    comedy_row = next(row for row in rows if row.key == "comedy")
    years = [comedies[idx - first_comedy]["year"] for idx in comedy_row.movie_idxs]
    assert years == [2012, 2016, 2005, 2006]  # 2010s first, then 2000s; each group by popularity


def test_browse_rows_skip_rows_too_short_to_look_like_a_row() -> None:
    movies = [movie(2015, ["Drama"]) for _ in range(MIN_ROW_SIZE - 1)]

    assert build_browse_rows(movies, np.ones(len(movies))) == []


def test_browse_rows_are_capped_and_show_each_movie_once() -> None:
    movies = [movie(2005, ["Action", "Comedy"]) for _ in range(3 * BROWSE_ROW_SIZE)]

    rows = build_browse_rows(movies, np.ones(len(movies)))

    shown = [idx for row in rows for idx in row.movie_idxs]
    assert [row.key for row in rows] == ["action", "comedy"]
    assert all(len(row.movie_idxs) == BROWSE_ROW_SIZE for row in rows)
    assert len(shown) == len(set(shown))


CATALOG = [movie(2000, ["Comedy"]) for _ in range(30)] + [movie(2000, ["Horror"]) for _ in range(30)]


def ranked(idxs: list[int]) -> list[Recommendation]:
    return [Recommendation(idx, 90) for idx in idxs]


def test_genre_rows_follow_the_picks_favourite_genres_and_skip_the_main_list() -> None:
    picks = [movie(2000, ["Horror"]), movie(2000, ["Horror"]), movie(2000, ["Comedy"])]
    main_list = list(range(20))  # comedies 0-19
    candidates = ranked([*main_list, *range(30, 60), *range(20, 30)])

    rows = build_genre_rows(picks, candidates, CATALOG, shown_above=set())

    assert [row.title for row in rows] == ["Because you love Horror", "Because you love Comedy"]
    assert rows[0].caption == GENRE_CAPTIONS["Horror"]
    assert [r.movie_idx for r in rows[0].recommendations] == list(range(30, 40))
    assert [r.movie_idx for r in rows[1].recommendations] == list(range(20, 30))


def test_genre_row_is_dropped_when_too_few_movies_are_left() -> None:
    picks = [movie(2000, ["Comedy"])]

    assert (
        build_genre_rows(picks, ranked(list(range(22))), CATALOG, shown_above=set()) == []
    )  # only 2 comedies past the main list


def test_every_genre_in_the_catalog_has_its_own_caption(artifacts: Artifacts) -> None:
    catalog_genres = {genre for movie in artifacts.movies_by_idx for genre in movie["genres"]} - NOT_A_GENRE

    assert catalog_genres <= set(GENRE_CAPTIONS)
