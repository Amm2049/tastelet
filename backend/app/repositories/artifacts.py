"""Loads everything the API needs from backend/artifacts. The only backend code that reads files."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from app.core.config import POPULARITY_EXPONENT
from app.ml.model import NCF, load_ncf

UNKNOWN_YEAR = 0  # only for hidden movies, which are never shown; gets no "prefer newer" boost


@dataclass(frozen=True)
class Artifacts:
    model: NCF
    movies_by_idx: list[dict[str, Any]]  # position = model's movie index
    movie_idx_by_id: dict[int, int]  # MovieLens id (used by the API) -> model index
    rating_counts: npt.NDArray[np.float64]  # ratings per movie index in the training data (= popularity)
    movie_years: npt.NDArray[np.int64]  # release year per movie index
    movie_idxs_by_collection: dict[int, list[int]]  # TMDB franchise id -> its shown movies' indices (v2)
    hidden_idxs: frozenset[int]  # no poster or no year (v3): never shown in picker, search or results
    negative_weights: npt.NDArray[np.float64]  # fold-in negative sampling weight per movie index
    unit_centroids: npt.NDArray[np.float64]  # (n_personas, dim), each row length 1
    personas: list[dict[str, Any]]  # position = persona id
    home_lists: dict[str, list[int]]  # list name -> MovieLens ids


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_showable(movie: dict[str, Any]) -> bool:
    """v1 dropped poster-less movies before training; the v3 model knows them, so the app hides them instead."""
    return bool(movie["poster"]) and movie["year"] is not None


def load_artifacts(artifacts_dir: Path) -> Artifacts:
    meta = _read_json(artifacts_dir / "movies_meta.json")
    movie_idx_by_id = {int(movie_id): idx for movie_id, idx in _read_json(artifacts_dir / "movie2idx.json").items()}

    movies_by_idx: list[dict[str, Any]] = [{}] * len(movie_idx_by_id)
    hidden_idxs: set[int] = set()
    for movie in meta["movies"]:
        idx = movie_idx_by_id[movie["id"]]
        if not is_showable(movie):
            hidden_idxs.add(idx)
        movies_by_idx[idx] = {**movie, "year": movie["year"] or UNKNOWN_YEAR}  # every year is an int from here on

    movie_idxs_by_collection: dict[int, list[int]] = {}
    for idx, movie in enumerate(movies_by_idx):
        if movie["collection_id"] is not None and idx not in hidden_idxs:
            movie_idxs_by_collection.setdefault(movie["collection_id"], []).append(idx)

    rating_counts = np.array(_read_json(artifacts_dir / "movie_rating_counts.json"), dtype=float)
    return Artifacts(
        model=load_ncf(artifacts_dir / "ncf_model.pt"),
        movies_by_idx=movies_by_idx,
        movie_idx_by_id=movie_idx_by_id,
        rating_counts=rating_counts,
        movie_years=np.array([movie["year"] for movie in movies_by_idx], dtype=np.int64),
        movie_idxs_by_collection=movie_idxs_by_collection,
        hidden_idxs=frozenset(hidden_idxs),
        negative_weights=rating_counts**POPULARITY_EXPONENT,
        unit_centroids=np.array(_read_json(artifacts_dir / "centroids.json")),
        personas=_read_json(artifacts_dir / "personas.json"),
        home_lists=meta["home_lists"],
    )
