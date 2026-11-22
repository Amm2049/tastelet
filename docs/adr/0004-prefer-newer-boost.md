# 0004. Small "prefer newer" boost on top of the model score (v2)

- Status: accepted
- Date: 2026-11-22
- Context of v2: built on branch `v2`, not deployed

## Context

Billy found that the results show "too many old movies". Checking it showed two causes:

1. **The picker** (main cause). v1 showed "Trending this week" (TMDB's 2026 trending list matched none of
   our movies, which end in 2018, so it silently fell back to "Most popular"), "Most popular" (mostly 90s
   classics) and "All-time favourites". Users could mostly only pick old movies, and the model correctly
   recommends movies like the picks. Fixed in v2 by new picker rows (recent hits first, genre rows with
   2010s movies first) and title search; see `backend/app/services/browse.py`.
2. **The ranking** is popularity-flavoured: newer movies had less time to collect ratings in MovieLens,
   so they score a little lower. That is what this ADR is about.

## Decision

Add a small bonus to every movie's model score before ranking:
`boost = NEWER_BOOST * clip((year - 1980) / (2018 - 1980), 0, 1)`, with `NEWER_BOOST = 0.3`.
So 1980 or older gets 0 and 2018 gets 0.3. Top scores are about 1–2 apart, so 0.3 mostly reorders
near-ties instead of overriding the user's taste. The picks get the same boost, so the match %
(ADR 0003) stays on one scale. Code: `newer_boosts` in `backend/app/services/recommender.py`.

## Measured (`notebooks/eval_newer_boost.py`, same Hit@10 as notebooks 03b and 04)

| Boost | Warm users Hit@10 | Cold start, 5 picks | Cold-start top 20 from 2010+ |
|---|---|---|---|
| 0 (v1) | 0.4667 | 0.41 | 7% |
| 0.1 | 0.4685 | 0.41 | 7% |
| 0.2 | 0.4685 | 0.41 | 8% |
| **0.3 (chosen)** | **0.4667** | **0.41** | **8%** |
| 0.5 | 0.4631 | 0.40 | 8% |
| 1.0 | 0.4631 | 0.39 | 11% |

Boost 0 reproduces `results.csv` exactly, so the comparison is fair.

## Alternatives

- **No boost:** simplest; the picker fix alone removes most of the "too old" feeling.
- **Bigger boost (≥ 0.5):** more 2010s movies, but Hit@10 starts to drop (cold start 0.41 → 0.39 at 1.0).
- **Retrain on newer data (`ml-32m`):** the only way to get movies after 2018; a project of its own.

## Consequences

- At 0.3, Hit@10 is unchanged, so `results.csv` stays valid for the report.
- The effect on recency is small (7% → 8% of results from 2010+). The report should say the picker
  change, not the boost, is what fixed "too old".
- Hit@10 cannot reward recency here: the test set is a random 10% of ratings, not the newest ones.
  It only shows that the boost does not hurt accuracy.
- Tested in `backend/tests/test_recommender.py` (0 up to 1980, half at 1999, full at 2018).
