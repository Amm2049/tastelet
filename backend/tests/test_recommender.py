import numpy as np
import pytest
import torch

from app.core.config import BLEND_W, N_CANDIDATES, N_RECOMMENDATIONS, NEWER_BOOST, SEED
from app.repositories.artifacts import Artifacts
from app.services.recommender import (
    UnknownMovieError,
    assign_persona,
    fan_start,
    fold_in_user_vector,
    match_percents,
    newer_boosts,
    recommend_for_picks,
    score_bonuses,
    to_movie_indices,
)

# MovieLens ids of the hand-made users from notebook 04.
ANIMATION_PICKS = [1, 364, 588, 6377, 4886]  # Toy Story, Lion King, Aladdin, Finding Nemo, Monsters Inc.
HORROR_PICKS = [1258, 1997, 1982, 1347, 2459]  # Shining, Exorcist, Halloween, Nightmare on Elm St, Texas Chainsaw
CRIME_90S_PICKS = [296, 1213, 1089, 6, 16]  # Pulp Fiction, Goodfellas, Reservoir Dogs, Heat, Casino
# v3 hand-made user (ADR 0006): Infinity War Part II (Endgame), Black Panther, Thor: Ragnarok, Guardians, Spider-Verse
MARVEL_PICKS = [122914, 122906, 122916, 112852, 195159]
PICK_SCORE_FLOOR = 4.0  # fan start reaches 4.36 for MARVEL_PICKS; the average-user start stayed at 0.6


def test_returns_twenty_recommendations_without_the_picks(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, ANIMATION_PICKS)

    recommended = {r.movie_idx for r in result.recommendations}
    picked = {artifacts.movie_idx_by_id[movie_id] for movie_id in ANIMATION_PICKS}
    assert len(result.recommendations) == N_RECOMMENDATIONS
    assert not recommended & picked


def test_same_picks_in_any_order_give_the_same_result(artifacts: Artifacts) -> None:
    first = recommend_for_picks(artifacts, CRIME_90S_PICKS)
    again_reordered = recommend_for_picks(artifacts, list(reversed(CRIME_90S_PICKS)))

    assert first == again_reordered


@pytest.mark.parametrize(
    ("picks", "persona_name"),
    [
        (MARVEL_PICKS, "The Blockbuster Hero"),
        (CRIME_90S_PICKS, "The Case Cracker"),
    ],  # only personas that fit: animation and horror picks land in unfitting ones (ADR 0007, known weakness)
)
def test_hand_made_users_get_fitting_personas(artifacts: Artifacts, picks: list[int], persona_name: str) -> None:
    result = recommend_for_picks(artifacts, picks)

    assert artifacts.personas[result.persona_id]["name"] == persona_name


def test_match_percents_are_between_0_and_100(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, HORROR_PICKS)

    assert all(0 <= r.match_percent <= 100 for r in result.recommendations)


def test_match_percents_are_relative_to_the_best_pick() -> None:
    scores = np.array([6.0, 4.0, 2.0, -1.0], dtype=np.float32)

    assert match_percents(scores, best_pick_score=4.0).tolist() == [100, 100, 50, 0]


def test_match_percents_use_a_floor_for_a_tiny_best_pick_score() -> None:
    scores = np.array([0.25], dtype=np.float32)

    assert match_percents(scores, best_pick_score=0.01).tolist() == [50]  # 0.25 / 0.5, not 0.25 / 0.01


def test_match_percents_spread_out_for_a_real_user(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, ANIMATION_PICKS)

    matches = [r.match_percent for r in result.recommendations]
    assert matches == sorted(matches, reverse=True)
    assert matches.count(100) <= 1


def test_unknown_movie_id_raises_with_the_bad_ids(artifacts: Artifacts) -> None:
    with pytest.raises(UnknownMovieError) as error:
        recommend_for_picks(artifacts, [*ANIMATION_PICKS[:4], 999_999_999])

    assert error.value.unknown_ids == [999_999_999]


def test_assign_persona_picks_the_closest_centroid() -> None:
    unit_centroids = np.array([[1.0, 0.0], [0.0, 1.0]])

    assert assign_persona(torch.tensor([[0.2, 3.0]]), unit_centroids) == 1


def test_newer_boost_is_zero_up_to_1980_and_full_at_2023() -> None:
    boosts = newer_boosts(np.array([1950, 1980, 2001, 2023, 2025]))

    linear_part = (2001 - 1980) / (2023 - 1980)
    assert boosts.tolist() == pytest.approx([0.0, 0.0, NEWER_BOOST * linear_part, NEWER_BOOST, NEWER_BOOST])


def test_ranked_candidates_extend_the_main_list(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, HORROR_PICKS)

    assert len(result.ranked) == N_CANDIDATES
    assert result.ranked[:N_RECOMMENDATIONS] == result.recommendations


def test_hidden_movies_are_never_recommended(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, HORROR_PICKS)

    assert artifacts.hidden_idxs  # v3 has movies without a poster or year
    assert not {recommendation.movie_idx for recommendation in result.ranked} & artifacts.hidden_idxs


def test_fan_start_is_the_mean_of_the_picks_fan_centroids() -> None:
    fan_centroids = np.array([[1.0, 0.0], [3.0, 2.0], [9.0, 9.0]], dtype=np.float32)

    start = fan_start([0, 1], fan_centroids)

    assert start.tolist() == [[2.0, 1.0]]


def test_fold_in_from_the_fans_lets_recent_picks_score_high(artifacts: Artifacts) -> None:
    # Regression (ADR 0006): from the average user, these picks stayed at ~0.6 whatever the learning rate.
    picks = to_movie_indices(MARVEL_PICKS, artifacts.movie_idx_by_id)
    start = fan_start(picks, artifacts.fan_centroids)

    user_vec = fold_in_user_vector(
        artifacts.model, picks, start, artifacts.negative_weights, np.random.default_rng(SEED)
    )

    with torch.no_grad():
        pick_scores = artifacts.model.score_vec(user_vec.expand(len(picks), -1), torch.tensor(picks))
    assert pick_scores.mean().item() > PICK_SCORE_FLOOR


def test_score_bonuses_add_the_newer_boost_and_the_popularity_blend() -> None:
    years = np.array([1980, 2023, 2023])
    scaled_popularity = np.array([0.0, 0.0, 1.0])

    bonuses = score_bonuses(years, scaled_popularity)

    assert bonuses.tolist() == pytest.approx([0.0, NEWER_BOOST, NEWER_BOOST + BLEND_W])
