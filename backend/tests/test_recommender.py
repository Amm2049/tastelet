import numpy as np
import pytest
import torch

from app.core.config import N_CANDIDATES, N_RECOMMENDATIONS, NEWER_BOOST
from app.repositories.artifacts import Artifacts
from app.services.recommender import (
    UnknownMovieError,
    assign_persona,
    match_percents,
    newer_boosts,
    recommend_for_picks,
)

# MovieLens ids of the hand-made users from notebook 04.
ANIMATION_PICKS = [1, 364, 588, 6377, 4886]  # Toy Story, Lion King, Aladdin, Finding Nemo, Monsters Inc.
HORROR_PICKS = [1258, 1997, 1982, 1347, 2459]  # Shining, Exorcist, Halloween, Nightmare on Elm St, Texas Chainsaw
CRIME_90S_PICKS = [296, 1213, 1089, 6, 16]  # Pulp Fiction, Goodfellas, Reservoir Dogs, Heat, Casino


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
        (ANIMATION_PICKS, "The Dreamer"),
        (HORROR_PICKS, "The Thrill Seeker"),
        (CRIME_90S_PICKS, "The Case Cracker"),
    ],
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


def test_newer_boost_is_zero_up_to_1980_and_full_at_2018() -> None:
    boosts = newer_boosts(np.array([1950, 1980, 1999, 2018, 2025]))

    assert boosts.tolist() == pytest.approx([0.0, 0.0, NEWER_BOOST / 2, NEWER_BOOST, NEWER_BOOST])


def test_ranked_candidates_extend_the_main_list(artifacts: Artifacts) -> None:
    result = recommend_for_picks(artifacts, HORROR_PICKS)

    assert len(result.ranked) == N_CANDIDATES
    assert result.ranked[:N_RECOMMENDATIONS] == result.recommendations
