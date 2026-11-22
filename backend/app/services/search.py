"""Title search for the picker (v2), so users can pick any movie in the catalog, not just the rows."""

from typing import Any

import numpy as np
import numpy.typing as npt

from app.core.config import MAX_SEARCH_LENGTH, MAX_SEARCH_RESULTS, MIN_SEARCH_LENGTH
from app.services.titles import display_title, search_key


def search_movies(query: str, movies_by_idx: list[dict[str, Any]], rating_counts: npt.NDArray[np.float64]) -> list[int]:
    """Movie indices whose title contains the query: titles starting with it first, then the most rated."""
    key = search_key(query[:MAX_SEARCH_LENGTH])  # cap: a huge query would be slow and can't match a title
    if len(key) < MIN_SEARCH_LENGTH:
        return []

    hits: list[tuple[bool, float, int]] = []
    for idx, movie in enumerate(movies_by_idx):
        title_key = search_key(display_title(movie["title"]))
        if key in title_key:
            # Sort key: prefix matches first, then more ratings, then index so ties are stable.
            hits.append((not title_key.startswith(key), -float(rating_counts[idx]), idx))
    return [idx for *_, idx in sorted(hits)[:MAX_SEARCH_RESULTS]]
