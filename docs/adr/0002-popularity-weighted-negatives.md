# 0002. Popularity-weighted negatives for the ranking model

- Status: accepted
- Date: 2026-10-27
- Issue: #11 (found during Phase 4, #10)
- Supersedes: the negative-sampling scheme in ADR 0001 (two models and 4 negatives per rating stay)

## Context

ADR 0001 trains the ranking model with 4 negatives per rating, sampled **uniformly** from
movies the user did not rate. In Phase 4 fold-in, three hand-made users with very different
tastes (family animation, classic horror, 90s crime) got nearly the same top 20: the
animation user got 0–2 animated films and mostly Shawshank, Forrest Gump and Matrix.

Diagnosis (notebook 04):

- Fold-in was not the cause. Trained users' own top 20s also overlapped the "average user"
  top 20 by 12.4/20, and folded-in vectors moved further from the mean (4.9–6.6) than real
  users do (median 2.4).
- Uniform negatives are mostly obscure movies (median 9 ratings). The model learned
  "popular = rated" and never saw "popular, but this user skipped it", so it mostly scores
  by popularity and barely uses the user vector.

## Decision

Sample training negatives with probability proportional to `rating_count ** 0.75`
(the word2vec trick: popular movies more often, without only ever the top few). Median rating
count of sampled negatives rises from 9 to 21. Everything else is unchanged: 4 negatives per
rating, label 0.5, dim 32, dropout 0.2, lr 1e-2, seed 42. Fold-in uses the same weighting for
its negatives. The new model replaces `ncf_model.pt`, now saved to `backend/artifacts/`.

## Alternatives

Measured in `notebooks/03b_popularity_negatives.ipynb`, 3 seeds (42, 1, 2), mean ± std.
"List overlap" = average number of top-20 movies two of 100 random users share (lower is more
personal).

| Negatives | Val Hit@10 | Test Hit@10 | List overlap |
|---|---|---|---|
| Uniform (ADR 0001) | 0.455 ± 0.012 | 0.449 ± 0.029 | 7.3 ± 1.0 |
| **Popularity-weighted** | 0.426 ± 0.039 | 0.454 ± 0.012 | **3.8 ± 2.0** |

Seed 42 (shipped): uniform 0.443 / 0.416 / 8.4, popular 0.382 / 0.467 / 2.5.

- **Popularity-weighted negatives only in fold-in.** No retraining, but hand-made users'
  lists stayed mostly generic (pairwise overlap 6–7.7/20). The model itself was the limit.
- **Re-rank by `score − α·log(popularity)` at serving time.** Removes popular movies but does
  not teach the model what a user likes; the animation user would get obscure films, not
  animation. Adds a knob to tune.

## Consequences

- Hit@10 is a tie within seed noise (val slightly lower, test slightly higher); both stay
  above popularity (0.3856). Lists are more personal on every seed.
- Hand-made users with the new model and popular fold-in negatives: pairwise overlap 1.3/20
  (was 9); animation user gets 7 animated films (Shrek, Shrek 2, Beauty and the Beast,
  Sleeping Beauty…). Horror stays weak (3/20): the horror classics have few ratings.
- `results.csv` keeps the old `ncf_ranking_4neg` row (Colab, Phase 3) and adds
  `ncf_ranking_popneg` (0.4667) for the shipped model.
- Training now runs locally (CPU, `.venv`) as well as in Colab. The local uniform model gets
  test Hit@10 0.416 vs 0.407 in Colab: same code, different hardware.
- **Limitation:** popular negatives are more likely to include movies a user would like but
  has not rated yet, so some "negatives" are wrong labels. Accepted for the gain in
  personalization.
- **Limitation:** list overlap varies a lot by seed (2.5–6.0 for popular); the direction is
  consistent, the size is not.
