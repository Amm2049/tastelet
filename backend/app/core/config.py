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

# "Prefer newer" boost (v2): added to the model score, growing linearly from 0 (FRESHNESS_FROM_YEAR or older)
# to NEWER_BOOST (FRESHNESS_TO_YEAR, the catalog's last year: 2023 since v3 uses ml-32m). Top scores sit ~1-2 apart,
# so 0.3 mostly reorders near-ties instead of overriding the user's taste (tried on the notebook 04 hand-made users).
NEWER_BOOST = 0.3
FRESHNESS_FROM_YEAR = 1980
FRESHNESS_TO_YEAR = 2023

# Results page (v2): genre rows are filled from the top N_CANDIDATES; each movie appears once per page.
N_CANDIDATES = 100
N_GENRE_ROWS = 3
GENRE_ROW_SIZE = 10
MIN_ROW_SIZE = 4
FRANCHISE_ROW_SIZE = 20  # no minimum: one sequel is still worth showing

# Picker rows (v2), Netflix-style: recent hits, one row per genre, Japanese animation after Animation (browse.py).
BROWSE_ROW_SIZE = 20
RECENT_FROM_YEAR = 2010
GENRE_ROW_FROM_YEAR = 2000
# One row per genre, titled with the genre's name, in this order.
BROWSE_GENRES = [
    "Action",
    "Animation",  # before Comedy, or Shrek and Nemo fill the comedy row
    "Comedy",
    "Sci-Fi",
    "Drama",
    "Thriller",
    "Horror",
]

MIN_SEARCH_LENGTH = 2
MAX_SEARCH_LENGTH = 100
MAX_SEARCH_RESULTS = 20
