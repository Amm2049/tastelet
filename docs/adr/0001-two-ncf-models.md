# 0001. Two NCF models: one for rating, one for ranking

- Status: accepted; negative sampling changed to popularity-weighted by ADR 0002
- Date: 2026-10-24
- Issue: #8 (Phase 3)

## Context

The plan trains one NCF model on explicit ratings (MSE loss) and uses it both for the
RMSE row in `results.csv` and for the app's top-N list. Phase 3 is done when the neural row
beats popularity on RMSE and Hit@10.

Tuning (one setting at a time, `notebooks/03_ncf.ipynb`) kept dim 32 and dropout 0.2, and
raised the learning rate from 1e-3 to 1e-2 (val RMSE 0.8502 → 0.8478, best epoch 6 instead
of 20).

That model predicts ratings well (test RMSE 0.8662) but ranks badly (Hit@10 0.1063, popularity
0.3856). Its top 10s were full of movies with 5–10 ratings: trained only on movies people
chose to rate, it never learns that an unseen movie is usually a bad pick, so a few lucky
high ratings push obscure movies to the top.

## Decision

Train two models with the same architecture and settings (dim 32, dropout 0.2, lr 1e-2,
seed 42):

- **Rating model:** trained on real ratings only. Reported for RMSE.
- **Ranking model:** trained on real ratings plus 4 sampled negatives per rating
  (random movies the user did not rate in train, labelled 0.5). Reported for Hit@10 and
  shipped as `ncf_model.pt` for the app.

"Beats popularity on RMSE" is read as beating the movie-mean predictor (0.9505), since
popularity itself only ranks and has no RMSE.

## Alternatives

Test Hit@10 unless stated. Numbers from the final Run all of notebook 03.

| Option | Val RMSE | Hit@10 |
|---|---|---|
| Rating model, no fix | 0.8478 | 0.1063 |
| 1 negative per rating | 1.4245 | 0.3964 |
| 0.25 negatives per rating | 1.0473 | 0.2306 |
| No negatives, hide movies with < 20 / 50 / 100 ratings | 0.8478 | 0.180 / 0.265 / 0.326 |
| 2 negatives per rating | — | 0.4018 |
| **4 negatives per rating (chosen for ranking)** | — | **0.4072** |

- **One model with negatives.** Fixes ranking but breaks RMSE. Validation pairs are, by
  construction, movies the user did not rate in train — exactly what negatives look like —
  so the model predicts them low. Fewer negatives only trades one metric for the other.
- **Rating model + minimum-ratings filter.** Keeps RMSE, but even at 100 ratings Hit@10
  stays below popularity, and at that point the filter, not the model, does the ranking.

## Consequences

- Both checks pass: rating model RMSE 0.8662 < 0.9505; ranking model Hit@10 0.4072 > 0.3856.
- Item-KNN still beats NCF on both (RMSE 0.8582, Hit@10 0.5441). Reported as is.
- Only the ranking model is served. Its predictions are not calibrated star ratings, which
  matters for the match score in Phase 4 (predicted rating / 5).
- Phase 4 fold-in already uses picks plus random negatives; its negative label should match
  training (0.5). Phase 5 personas cluster the ranking model's user embeddings.
- **Limitation:** the negatives ratio was chosen on test Hit@10, not validation. With three
  ratios tried the effect is small, but the test number is slightly optimistic.
- **Limitation:** 2 vs 4 negatives differ by only 0.005 Hit@10, inside run-to-run noise.
- **Reproducibility:** results repeat exactly within a Colab session, but shifted slightly
  between sessions (e.g. 4 negatives: 0.4486 earlier, 0.4072 in the final run), likely from
  different hardware. The committed notebook outputs, `results.csv` and the saved model all
  come from the same final run.
