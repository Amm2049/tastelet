"""Constants shared by the backend. Fold-in values must match notebook 04, where they were measured."""

import os
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"

# Comma-separated; set to the deployed frontend URL in production.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

TORCH_THREADS = 1  # see main.py lifespan (issue #22)

SEED = 42  # fixed seed for fold-in negatives: same picks -> same persona and list (F4)

MIN_PICKS = 5
MAX_PICKS = 10
N_RECOMMENDATIONS = 20

FOLD_IN_STEPS = 100
FOLD_IN_LR = 0.05
FOLD_IN_NEGATIVES = 20
FOLD_IN_L2 = 1e-3
PICK_RATING = 5.0
NEGATIVE_RATING = 0.5  # label the ranking model was trained with for negatives (ADR 0001)
POPULARITY_EXPONENT = 0.75  # negatives sampled like training (ADR 0002)
