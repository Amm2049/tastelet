from pathlib import Path

import torch

from app.ml.model import load_ncf

CHECKPOINT_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "ncf_model.pt"


def test_load_ncf_rebuilds_the_trained_model() -> None:
    model = load_ncf(CHECKPOINT_PATH)

    assert model.user_embedding.num_embeddings == 200_948
    assert model.movie_embedding.num_embeddings == 23_344
    assert not model.training
    assert not any(p.requires_grad for p in model.parameters())


def test_score_vec_matches_forward_for_trained_users() -> None:
    model = load_ncf(CHECKPOINT_PATH)
    users = torch.tensor([0, 1, 2])
    movies = torch.tensor([10, 20, 30])

    via_forward = model(users, movies)
    via_vec = model.score_vec(model.user_embedding(users), movies)

    assert torch.equal(via_forward, via_vec)
