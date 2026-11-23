from typing import Any

import pytest

from app.core.config import FRANCHISE_ROW_SIZE
from app.services.recommender import Recommendation
from app.services.result_rows import (
    FRANCHISE_ROW_TITLE,
    build_franchise_row,
    build_genre_rows,
    franchise_name,
    join_names,
)

TOY_STORY, SHREK = 10, 20


def movie(collection_id: int | None = None, name: str | None = None) -> dict[str, Any]:
    return {"collection_id": collection_id, "collection_name": name, "genres": ["Comedy"], "year": 2005}


# idx 0-2: Toy Story 1-3; idx 3-4: Shrek 1-2; idx 5: no franchise
CATALOG = [
    movie(TOY_STORY, "Toy Story Collection"),
    movie(TOY_STORY, "Toy Story Collection"),
    movie(TOY_STORY, "Toy Story Collection"),
    movie(SHREK, "Shrek Collection"),
    movie(SHREK, "Shrek Collection"),
    movie(),
]
BY_COLLECTION = {TOY_STORY: [0, 1, 2], SHREK: [3, 4]}
MATCHES = [0, 40, 90, 0, 60, 0]  # match % per movie


def test_franchise_row_lists_the_unpicked_sequels_best_match_first() -> None:
    row = build_franchise_row([0, 3, 5], CATALOG, BY_COLLECTION, MATCHES)

    assert row is not None
    assert row.title == FRANCHISE_ROW_TITLE
    assert [(r.movie_idx, r.match_percent) for r in row.recommendations] == [(2, 90), (4, 60), (1, 40)]
    assert row.caption == "Because you picked Shrek and Toy Story."


def test_franchise_row_is_the_same_for_picks_in_any_order() -> None:
    assert build_franchise_row([5, 3, 0], CATALOG, BY_COLLECTION, MATCHES) == build_franchise_row(
        [0, 3, 5], CATALOG, BY_COLLECTION, MATCHES
    )


def test_franchise_row_skips_franchises_the_user_picked_completely() -> None:
    row = build_franchise_row([3, 4, 0], CATALOG, BY_COLLECTION, MATCHES)

    assert row is not None
    assert row.caption == "Because you picked Toy Story."  # both Shrek movies are picks, nothing left to add
    assert {r.movie_idx for r in row.recommendations} == {1, 2}


def test_no_franchise_row_without_franchise_picks() -> None:
    assert build_franchise_row([5], CATALOG, BY_COLLECTION, MATCHES) is None


def test_franchise_row_is_capped() -> None:
    big = 1
    catalog = [movie(big, "Big Collection") for _ in range(FRANCHISE_ROW_SIZE + 5)]

    row = build_franchise_row([0], catalog, {big: list(range(len(catalog)))}, [50] * len(catalog))

    assert row is not None
    assert len(row.recommendations) == FRANCHISE_ROW_SIZE


@pytest.mark.parametrize(
    ("names", "text"),
    [(["Alien"], "Alien"), (["Alien", "Shrek"], "Alien and Shrek"), (["A", "B", "C"], "A, B and C")],
)
def test_join_names(names: list[str], text: str) -> None:
    assert join_names(names) == text


def test_franchise_name_drops_the_collection_suffix() -> None:
    assert franchise_name("Toy Story Collection") == "Toy Story"
    assert franchise_name("The Lord of the Rings Collection") == "The Lord of the Rings"


def test_genre_rows_skip_movies_already_in_the_franchise_row() -> None:
    catalog = [movie() for _ in range(40)]
    ranked = [Recommendation(idx, 50) for idx in range(40)]  # 0-19 are the main list

    rows = build_genre_rows([catalog[0]], ranked, catalog, shown_above={20, 21})

    assert [r.movie_idx for r in rows[0].recommendations][:2] == [22, 23]
