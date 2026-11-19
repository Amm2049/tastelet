# 0003. Match score relative to the user's best pick

- Status: accepted
- Date: 2026-11-19
- Issue: #18 (found in the Phase 7 browser check)

## Context

The plan shows each recommendation's match score as `predicted score / 5`, clipped to 0–100%.
The ranking model's scores are not calibrated star ratings (ADR 0001): across all movies the median
is about 0.8 and the top recommendations reach 4–6. For a user who picks popular films
(Forrest Gump, Silence of the Lambs, Jurassic Park, Schindler's List, American Beauty) the whole
first row of the result page read "100% match", which looks broken in a demo.

## Decision

`match = score / best_pick_score`, clipped to 0–100%, where `best_pick_score` is the highest score any
of the user's own picks gets after fold-in. "100%" now means "scores as high as your strongest pick".
The reference has a floor of 0.5 (the negative label) so a badly fitted fold-in cannot inflate every
match to 100%. Code: `match_percents` in `backend/app/services/recommender.py`.

## Alternatives

| Option | Popular-picks user, top 20 | Animation user, top 20 |
|---|---|---|
| Plan: score / 5 | many 100% | 99, 81, 80, … |
| **Score / best pick (chosen)** | 100 → 75 | 97 → 60 |
| Percentile among all movies | all ≈ 99–100% | all ≈ 99–100% |

- **Percentile rank:** honest, but the top 20 of 3,636 movies are all above the 99th percentile.
- **Keep score / 5:** no change, but the screen looks broken for common tastes.

## Consequences

- Match scores now differ within a list and still follow the ranking (it is a monotonic rescale, so
  the order of recommendations is unchanged).
- It is still not a probability or a predicted rating; the report should say so.
- Tested in `backend/tests/test_recommender.py` (relative scale, floor, spread for a real user).
