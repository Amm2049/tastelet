"""The favourite-genre sentence shown with the results (plan, Phase 6 step 1)."""

from collections import Counter
from typing import Any

NOT_A_GENRE = {"IMAX", "(no genres listed)"}  # IMAX is a format tag, not a taste


def decade_of(year: int) -> int:
    return year // 10 * 10


def top_by_count(counts: Counter[Any], n: int) -> list[Any]:
    # Ties break by value (alphabetical / earliest decade), so the same picks always give the same sentence.
    return [value for value, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:n]]


def genre_sentence(picked_movies: list[dict[str, Any]]) -> str:
    genre_counts = Counter(genre for movie in picked_movies for genre in movie["genres"] if genre not in NOT_A_GENRE)
    decade = top_by_count(Counter(decade_of(movie["year"]) for movie in picked_movies), 1)[0]
    top_genres = top_by_count(genre_counts, 2)

    if len(top_genres) == 2:
        genres_text = f"{top_genres[0]} and {top_genres[1]}"
    elif top_genres:
        genres_text = top_genres[0]
    else:
        return f"You gravitate toward films from the {decade}s."
    return f"You gravitate toward {genres_text}, especially films from the {decade}s."
