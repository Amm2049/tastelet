# 0005. Blend a little popularity into the cold-start score (v3)

- Status: accepted
- Date: 2026-11-23
- Context of v3: model retrained on MovieLens `ml-32m` with a per-user time split (branch `v3`, not deployed)

## Context

On v3, the app's cold start (fold-in from 5 picks, then rank by model score) **lost to plain
popularity**: test Hit@10 0.159 vs 0.211 (1,000 test users, noise about ±0.013). In v1 it won
(0.41 vs 0.36), but v1 used a random split, where test movies came from every period.

What we ruled out first (all in the Colab notebook `v3_02_train`, on 300 val users):

1. **Fold-in stopping too early.** Pick scores were 3.0 instead of 5.0 and vectors shorter than trained
   users (14.6 vs 24.1). More steps and a higher learning rate raised the pick scores (up to 3.8) but not
   Hit@10 (0.16–0.18), so the fold-in settings stay unchanged. (The smaller-L2 run gave numbers identical
   to plain 300 steps; a notebook edit may have kept the old L2, so that row is not trusted.)
2. **Which 5 picks we use.** Top-rated (old classics) 0.170, most recent likes 0.190, random likes 0.170:
   all inside the noise, all below popularity (0.207).
3. **The "prefer newer" boost (ADR 0004).** It does not help (0.170 → 0.163 at 0.3, 0.147 at 1.0).

The cold-start lists were also generic (1,149 different movies across 1,000 users' top 10,
vs 3,662 with full history): 5 picks carry too little signal, and users' next likes are often popular.

## Decision

Add a scaled popularity term to the cold-start score before ranking:
`score = model score + BLEND_W * log1p(rating_count) / max(log1p(rating_count))`, with **`BLEND_W = 4`**.
The log tames the skew (a few movies have tens of thousands of ratings); dividing by the maximum puts it in 0..1.

`w` was chosen on **val** users only (accuracy) plus list variety (which uses no test likes), then
checked **once** on test.

## Measured

Val Hit@10 (1,000 val users) and variety (different movies in the top 10 of 1,000 test users):

| w | Val Hit@10 | Different movies | Median rating count of results |
|---|---|---|---|
| 0 (no blend) | 0.142 | 1,149 | 13,358 |
| 2 | – | 853 | 26,210 |
| **4 (chosen)** | **0.199** | **596** | **37,916** |
| 8 | 0.213 | 338 | 50,879 |
| 16 (val peak) | 0.231 | 189 | 61,404 |
| 32 | 0.206 | – | – |
| 100 | 0.198 | – | – |
| plain popularity | 0.200 | 132 | 66,650 |

Test Hit@10 (1,000 test users, 5 top-rated train movies as picks): popularity 0.211 ·
no blend 0.159 · **blend w 4: 0.226** · blend w 16: 0.247 · trained embedding (full history) 0.233.

## Alternatives

- **No blend:** most personal lists, but cold start loses clearly to popularity (0.159 vs 0.211).
- **w = 16 (best accuracy):** 0.247 on test, but only 189 different movies across 1,000 users,
  barely more than popularity's 132: nearly one popular list for everyone. That breaks the app's
  promise of a taste-based list; Hit@10 alone hides it.
- **w = 8:** a bit more accurate than w = 4, but variety drops to 338.
- **Bigger model (embedding dim 64):** not tried; the full-history model already beats popularity,
  so the weakness is cold start, not the model.

## Consequences

- The app matches/beats popularity on accuracy (test 0.226 vs 0.211) while keeping lists personal
  (596 vs 132 different movies).
- Results lean more popular (median rating count 13k → 38k). Fine for the "Top picks" list; the genre and
  franchise rows still come from the same blended ranking.
- Backend (step 7): add `BLEND_W` to `core/config.py`, store per-movie scaled popularity in the artifacts,
  add it in `rank_movies`, with a unit test. The match % (ADR 0003) must use the same blended score for
  the picks so it stays on one scale.
- `FRESHNESS_TO_YEAR` (ADR 0004) must become 2023, the last year of the `ml-32m` catalog.
- ADR 0006 later changed the fold-in start (picks' fans); w = 4 stays (fan start val: w 4 0.232, w 8 0.233).
- The report should show both numbers (accuracy and variety) and why the highest-scoring `w` was not chosen.
