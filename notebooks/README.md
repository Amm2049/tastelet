# Notebooks (Phases 1-5, run in Colab)

| Notebook | Phase | Output |
| --- | --- | --- |
| 01_data_prep.ipynb | 1 Data prep | splits, user2idx/movie2idx, movies_meta.json |
| 02_baselines.ipynb | 2 Baselines | results/results.csv rows |
| 03_model.ipynb | 3 Neural model | backend/artifacts/ncf_model.pt, loss curves |
| 04_foldin_personas.ipynb | 4-5 Fold-in + personas | centroids.json, personas.json |

Rule: explore here, then move code that works into `ml/` (tested) and import it back.
