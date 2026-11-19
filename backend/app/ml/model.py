"""NCF ranking model: one definition shared by training notebooks and the API."""

from pathlib import Path

import torch
from torch import nn

HIDDEN_UNITS = (64, 32)


class NCF(nn.Module):
    def __init__(self, n_users: int, n_movies: int, dim: int, dropout: float) -> None:
        super().__init__()
        self.user_embedding = nn.Embedding(n_users, dim)
        self.movie_embedding = nn.Embedding(n_movies, dim)
        first, second = HIDDEN_UNITS
        self.mlp = nn.Sequential(
            nn.Linear(2 * dim, first),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(first, second),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(second, 1),
        )

    def score_vec(self, user_vecs: torch.Tensor, movie_ids: torch.Tensor) -> torch.Tensor:
        # Takes user vectors directly, so a folded-in user (not in the embedding table) can be scored.
        pair = torch.cat([user_vecs, self.movie_embedding(movie_ids)], dim=1)
        scores: torch.Tensor = self.mlp(pair).squeeze(-1)
        return scores

    def forward(self, user_ids: torch.Tensor, movie_ids: torch.Tensor) -> torch.Tensor:
        return self.score_vec(self.user_embedding(user_ids), movie_ids)


def load_ncf(checkpoint_path: Path) -> NCF:
    """Rebuild the model from the checkpoint saved by notebook 03b, ready for serving."""
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model = NCF(checkpoint["n_users"], checkpoint["n_movies"], checkpoint["embedding_dim"], checkpoint["dropout"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()  # turns dropout off
    model.requires_grad_(False)  # weights never change while serving; fold-in only trains its own user vector
    return model
