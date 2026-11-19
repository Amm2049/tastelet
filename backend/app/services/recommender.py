"""Cold-start recommendations: fold in a new user from their picks, rank movies, assign a persona.

Same method and numbers as notebook 04 (fold-in, ranking) and its persona cells (Phase 5).
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import torch
from torch import nn

from app.core.config import (
    FOLD_IN_L2,
    FOLD_IN_LR,
    FOLD_IN_NEGATIVES,
    FOLD_IN_STEPS,
    N_RECOMMENDATIONS,
    NEGATIVE_RATING,
    PICK_RATING,
    SEED,
)
from app.ml.model import NCF
from app.repositories.artifacts import Artifacts


class UnknownMovieError(ValueError):
    def __init__(self, unknown_ids: list[int]) -> None:
        super().__init__(f"Unknown movie id(s): {', '.join(map(str, unknown_ids))}")
        self.unknown_ids = unknown_ids


@dataclass(frozen=True)
class Recommendation:
    movie_idx: int
    match_percent: int


@dataclass(frozen=True)
class RecommendationResult:
    persona_id: int
    recommendations: list[Recommendation]


def to_movie_indices(movie_ids: list[int], movie_idx_by_id: dict[int, int]) -> list[int]:
    unknown_ids = [movie_id for movie_id in movie_ids if movie_id not in movie_idx_by_id]
    if unknown_ids:
        raise UnknownMovieError(unknown_ids)
    # Sorted so the same picks in a different order give exactly the same result.
    return sorted(movie_idx_by_id[movie_id] for movie_id in movie_ids)


def fold_in_user_vector(
    model: NCF, picks: list[int], negative_weights: npt.NDArray[np.float64], rng: np.random.Generator
) -> torch.Tensor:
    """Learn one user vector (model frozen) so picks score PICK_RATING and sampled other movies NEGATIVE_RATING."""
    user_vec = nn.Parameter(model.user_embedding.weight.mean(dim=0, keepdim=True).clone())
    optimizer = torch.optim.Adam([user_vec], lr=FOLD_IN_LR)

    unpicked = np.setdiff1d(np.arange(len(negative_weights)), picks)
    probs = negative_weights[unpicked] / negative_weights[unpicked].sum()
    negatives = rng.choice(unpicked, size=FOLD_IN_NEGATIVES, replace=False, p=probs)
    movie_ids = torch.tensor(np.concatenate([picks, negatives]), dtype=torch.long)
    targets = torch.tensor([PICK_RATING] * len(picks) + [NEGATIVE_RATING] * FOLD_IN_NEGATIVES)

    for _ in range(FOLD_IN_STEPS):
        optimizer.zero_grad()
        predicted = model.score_vec(user_vec.expand(len(movie_ids), -1), movie_ids)
        loss = ((predicted - targets) ** 2).mean() + FOLD_IN_L2 * (user_vec**2).sum()
        loss.backward()  # type: ignore[no-untyped-call]  # torch ships this method untyped
        optimizer.step()
    return user_vec.detach()


def match_percents(scores: npt.NDArray[np.float32], best_pick_score: float) -> npt.NDArray[np.int64]:
    """100% = scores as high as the user's best-scoring pick (ADR 0003).

    The ranking model's scores are not calibrated ratings, so the plan's score / 5 showed many 100%s.
    The floor stops a tiny best-pick score from blowing every match up to 100%.
    """
    reference = max(best_pick_score, NEGATIVE_RATING)
    return np.clip(scores / reference * 100, 0, 100).round().astype(np.int64)


def top_recommendations(model: NCF, user_vec: torch.Tensor, picks: list[int]) -> list[Recommendation]:
    n_movies = model.movie_embedding.num_embeddings
    with torch.no_grad():
        scores = model.score_vec(user_vec.expand(n_movies, -1), torch.arange(n_movies)).numpy()
    best_pick_score = float(scores[picks].max())
    scores[picks] = -np.inf  # never recommend a movie the user already picked
    top = np.argsort(-scores, kind="stable")[:N_RECOMMENDATIONS]  # stable: ties break the same way every run
    matches = match_percents(scores[top], best_pick_score)
    return [Recommendation(int(idx), int(match)) for idx, match in zip(top, matches, strict=True)]


def assign_persona(user_vec: torch.Tensor, unit_centroids: npt.NDArray[np.float64]) -> int:
    unit_vec = user_vec.numpy().ravel() / np.linalg.norm(user_vec.numpy())
    return int(np.argmax(unit_centroids @ unit_vec))  # unit vectors: largest dot product = nearest centroid


def recommend_for_picks(artifacts: Artifacts, movie_ids: list[int]) -> RecommendationResult:
    picks = to_movie_indices(movie_ids, artifacts.movie_idx_by_id)
    rng = np.random.default_rng(SEED)  # new per request: deterministic and safe with concurrent requests
    user_vec = fold_in_user_vector(artifacts.model, picks, artifacts.negative_weights, rng)
    return RecommendationResult(
        persona_id=assign_persona(user_vec, artifacts.unit_centroids),
        recommendations=top_recommendations(artifacts.model, user_vec, picks),
    )
