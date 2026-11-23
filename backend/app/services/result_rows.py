"""Extra rows for the Netflix-style results page (v2), under the main list (the hero + "Top picks for you").

- "More from your franchises": the other movies of the picks' TMDB franchises, like Netflix's
  "Because you watched X". The main list stays the model's pure taste ranking; this row only makes sure
  sequels and prequels are easy to find, so it may repeat a movie that is already in the main list.
- "Because you love <genre>" rows with a fun caption; they skip every movie shown above them.
"""

from dataclasses import dataclass
from typing import Any

from app.core.config import FRANCHISE_ROW_SIZE, GENRE_ROW_SIZE, MIN_ROW_SIZE, N_GENRE_ROWS, N_RECOMMENDATIONS
from app.services.genre_sentence import favourite_genres
from app.services.recommender import Recommendation

FRANCHISE_ROW_TITLE = "More from your franchises"
GENRE_CAPTIONS = {
    "Action": "Big explosions, bigger heroes.",
    "Adventure": "Pack your bags, the journey starts here.",
    "Animation": "Drawn to your taste, frame by frame.",
    "Children": "Family movie night, sorted.",
    "Comedy": "Guaranteed laughs, ranked for you.",
    "Crime": "Cases worth cracking tonight.",
    "Documentary": "True stories, stranger than fiction.",
    "Drama": "Stories that stay with you.",
    "Fantasy": "Worlds beyond this one.",
    "Film-Noir": "Shadows, smoke and secrets.",
    "Horror": "Lights off. Volume up. Don't look behind you.",
    "Musical": "Hit play and sing along.",
    "Mystery": "Clues for the curious mind.",
    "Romance": "For the hopeless romantic in you.",
    "Sci-Fi": "Futures worth visiting.",
    "Thriller": "Edge-of-your-seat picks.",
    "War": "Courage under fire.",
    "Western": "Saddle up, partner.",
}
DEFAULT_CAPTION = "More picks that fit your taste."


@dataclass(frozen=True)
class ResultRow:
    title: str
    caption: str
    recommendations: list[Recommendation]


def franchise_name(collection_name: str) -> str:
    """'Toy Story Collection' -> 'Toy Story'."""
    return collection_name.removesuffix(" Collection")


def join_names(names: list[str]) -> str:
    """['A'] -> 'A'; ['A', 'B', 'C'] -> 'A, B and C'."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def build_franchise_row(
    picks: list[int],
    movies_by_idx: list[dict[str, Any]],
    movie_idxs_by_collection: dict[int, list[int]],
    match_by_idx: list[int],
) -> ResultRow | None:
    """The picks' franchise movies the user did not pick, best match first; None if there are none."""
    picked = set(picks)
    siblings_by_name: dict[str, list[int]] = {}
    for pick in picks:
        collection_id = movies_by_idx[pick]["collection_id"]
        siblings = [idx for idx in movie_idxs_by_collection.get(collection_id, []) if idx not in picked]
        if siblings:
            siblings_by_name[franchise_name(movies_by_idx[pick]["collection_name"])] = siblings

    # Sorted, so the same picks in any order give the same row and caption.
    idxs = sorted(
        {idx for siblings in siblings_by_name.values() for idx in siblings}, key=lambda i: (-match_by_idx[i], i)
    )
    if not idxs:
        return None
    caption = f"Because you picked {join_names(sorted(siblings_by_name))}."
    return ResultRow(
        FRANCHISE_ROW_TITLE, caption, [Recommendation(idx, match_by_idx[idx]) for idx in idxs[:FRANCHISE_ROW_SIZE]]
    )


def build_genre_rows(
    picked_movies: list[dict[str, Any]],
    ranked: list[Recommendation],
    movies_by_idx: list[dict[str, Any]],
    shown_above: set[int],
) -> list[ResultRow]:
    """One row per favourite genre of the picks, best-ranked first, skipping the main list and `shown_above`."""
    shown = {recommendation.movie_idx for recommendation in ranked[:N_RECOMMENDATIONS]} | shown_above
    rows: list[ResultRow] = []
    for genre in favourite_genres(picked_movies, N_GENRE_ROWS):
        in_genre = [
            recommendation
            for recommendation in ranked
            if recommendation.movie_idx not in shown and genre in movies_by_idx[recommendation.movie_idx]["genres"]
        ][:GENRE_ROW_SIZE]
        if len(in_genre) >= MIN_ROW_SIZE:
            rows.append(ResultRow(f"Because you love {genre}", GENRE_CAPTIONS.get(genre, DEFAULT_CAPTION), in_genre))
            shown.update(recommendation.movie_idx for recommendation in in_genre)
    return rows
