"""Loads everything the API needs from backend/artifacts. The only backend code that reads files."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from app.core.config import POPULARITY_EXPONENT
from app.ml.model import NCF, load_ncf


@dataclass(frozen=True)
class Artifacts:
    model: NCF
    movies_by_idx: list[dict[str, Any]]  # position = model's movie index
    movie_idx_by_id: dict[int, int]  # MovieLens id (used by the API) -> model index
    negative_weights: npt.NDArray[np.float64]  # fold-in negative sampling weight per movie index
    unit_centroids: npt.NDArray[np.float64]  # (n_personas, dim), each row length 1
    personas: list[dict[str, Any]]  # position = persona id
    home_lists: dict[str, list[int]]  # list name -> MovieLens ids


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifacts(artifacts_dir: Path) -> Artifacts:
    meta = _read_json(artifacts_dir / "movies_meta.json")
    movie_idx_by_id = {int(movie_id): idx for movie_id, idx in _read_json(artifacts_dir / "movie2idx.json").items()}

    movies_by_idx: list[dict[str, Any]] = [{}] * len(movie_idx_by_id)
    for movie in meta["movies"]:
        movies_by_idx[movie_idx_by_id[movie["id"]]] = movie

    rating_counts = np.array(_read_json(artifacts_dir / "movie_rating_counts.json"), dtype=float)
    return Artifacts(
        model=load_ncf(artifacts_dir / "ncf_model.pt"),
        movies_by_idx=movies_by_idx,
        movie_idx_by_id=movie_idx_by_id,
        negative_weights=rating_counts**POPULARITY_EXPONENT,
        unit_centroids=np.array(_read_json(artifacts_dir / "centroids.json")),
        personas=_read_json(artifacts_dir / "personas.json"),
        home_lists=meta["home_lists"],
    )
