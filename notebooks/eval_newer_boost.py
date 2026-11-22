"""Hit@10 with and without the v2 "prefer newer" boost (ADR 0004).

Uses the exact Hit@10 definitions of notebook 03b (warm users, shipped ranking model) and notebook 04
(cold start: 100 test users, their 5 best-rated train movies as picks), so boost 0.0 must reproduce
results.csv (0.4667 and 0.41). Prints a table; writes nothing.

Run from backend/:  PYTHONPATH=. python ../notebooks/eval_newer_boost.py <data/processed folder>
"""

import sys
from collections.abc import Callable

import numpy as np
import pandas as pd
import torch

from app.core.config import ARTIFACTS_DIR, NEWER_BOOST, SEED
from app.repositories.artifacts import load_artifacts
from app.services.recommender import fold_in_user_vector, newer_boosts

TOP_K = 10
LIKED_RATING = 4.0
N_COLD_START_USERS = 100
N_COLD_START_PICKS = 5
N_RECOMMENDATIONS = 20
BOOST_STRENGTHS = [0.0, 0.1, 0.2, NEWER_BOOST, 0.5, 1.0]
RECENT_FROM_YEAR = 2010


def hit_at_10(score_fn: Callable[[int], np.ndarray], train_df: pd.DataFrame, test_df: pd.DataFrame) -> float:
    """Share of test users with at least one liked test movie in their top 10 (as in notebooks 03b/04)."""
    seen_by_user = train_df.groupby("user_idx")["movie_idx"].apply(set)
    liked_by_user = test_df[test_df["rating"] >= LIKED_RATING].groupby("user_idx")["movie_idx"].apply(set)
    hits = 0
    for user_idx, liked_movies in liked_by_user.items():
        scores = np.asarray(score_fn(user_idx), dtype=float).copy()
        scores[list(seen_by_user.get(user_idx, set()))] = -np.inf  # never recommend a movie rated in train
        if liked_movies & set(np.argpartition(-scores, TOP_K)[:TOP_K].tolist()):
            hits += 1
    return hits / len(liked_by_user)


def main(data_dir: str) -> None:
    torch.set_num_threads(1)
    artifacts = load_artifacts(ARTIFACTS_DIR)
    model = artifacts.model
    n_movies = model.movie_embedding.num_embeddings
    all_movies = torch.arange(n_movies)
    train_df = pd.read_csv(f"{data_dir}/ratings_train.csv")
    test_df = pd.read_csv(f"{data_dir}/ratings_test.csv")
    assert (np.bincount(train_df["movie_idx"], minlength=n_movies) == artifacts.rating_counts).all()

    with torch.no_grad():
        warm = {u: model(torch.full((n_movies,), u), all_movies).numpy() for u in test_df["user_idx"].unique()}

    users_with_likes = np.sort(test_df.loc[test_df["rating"] >= LIKED_RATING, "user_idx"].unique())
    cold_users = np.random.default_rng(SEED).choice(users_with_likes, size=N_COLD_START_USERS, replace=False)
    cold_test_df = test_df[test_df["user_idx"].isin(cold_users)]
    seen_by_user = train_df.groupby("user_idx")["movie_idx"].apply(set)
    cold = {}
    for user_idx in cold_users:
        picks = train_df[train_df["user_idx"] == user_idx].nlargest(N_COLD_START_PICKS, "rating")["movie_idx"].tolist()
        user_vec = fold_in_user_vector(model, picks, artifacts.negative_weights, np.random.default_rng(SEED))
        with torch.no_grad():
            cold[user_idx] = model.score_vec(user_vec.expand(n_movies, -1), all_movies).numpy()

    unit_boost = newer_boosts(artifacts.movie_years) / NEWER_BOOST
    print("boost | warm Hit@10 | cold-start Hit@10 | cold top-20 from 2010+")
    for strength in BOOST_STRENGTHS:
        boost = strength * unit_boost
        warm_hit = hit_at_10(lambda u, b=boost: warm[u] + b, train_df, test_df)
        cold_hit = hit_at_10(lambda u, b=boost: cold[u] + b, train_df, cold_test_df)
        years = []
        for user_idx in cold_users:
            scores = cold[user_idx] + boost
            scores[list(seen_by_user[user_idx])] = -np.inf
            years += artifacts.movie_years[np.argsort(-scores, kind="stable")[:N_RECOMMENDATIONS]].tolist()
        recent_share = np.mean(np.array(years) >= RECENT_FROM_YEAR)
        print(f"{strength:5.1f} | {warm_hit:11.4f} | {cold_hit:17.4f} | {recent_share:.0%}")


if __name__ == "__main__":
    main(sys.argv[1])
