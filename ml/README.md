# ml/ — reusable training code

Code that graduates from notebooks lands here, with tests:
- `data.py` — load, clean, re-index, split (pure functions)
- `evaluate.py` — `rmse`, `hit_at_10` (used by every model)
- `baselines.py` — global mean, popularity, item-KNN
- `train.py` — NCF training loop, saves artifacts

The NCF model class lives in `backend/app/ml/model.py` so training and serving share one definition.
