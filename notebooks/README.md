# Notebooks (Phases 1-5)

| Notebook | Phase | Output |
| --- | --- | --- |
| 01_data_prep.ipynb | 1 Data prep | splits, user2idx/movie2idx, movies_meta.json |
| 02_baselines.ipynb | 2 Baselines | results/results.csv rows |
| 03_ncf.ipynb | 3 Neural model | rating + ranking models, loss curve (ADR 0001) |
| 03b_popularity_negatives.ipynb | #11 fix | backend/artifacts/ncf_model.pt, popneg row (ADR 0002) |
| 04_fold_in_personas.ipynb | 4-5 Fold-in + personas | cold-start Hit@10 row; centroids.json, personas.json (Phase 5) |

Notebooks 01-03 run in Colab. From 03b on they also run locally: put the processed files from
Drive into `data/processed/`, create `.venv`, then run from `notebooks/`.

Rule: explore here, then move code that works into `ml/` (tested) and import it back.
