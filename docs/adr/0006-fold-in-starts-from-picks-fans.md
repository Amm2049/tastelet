# 0006. Start the fold-in from the picks' fans, not the average user (v3)

- Status: accepted
- Date: 2026-11-23
- Context of v3: model retrained on MovieLens `ml-32m` with a per-user time split (branch `v3`, not deployed)

## Context

After the popularity blend (ADR 0005), we looked at real lists for three hand-made users
(Colab notebook `v3_02_train`, fold-in + blend w = 4 + newer boost 0.3). A Marvel fan
(Infinity War Part II, Black Panther, Thor: Ragnarok, Guardians of the Galaxy, Into the Spider-Verse)
got Fight Club, Office Space and American Beauty, and not one superhero movie. A horror fan got
almost no horror. Hit@10 had not shown this.

What we checked, one hypothesis at a time:

1. **Time split starved recent movies?** No: about 80% of each pick's ratings are in train (6k–22k each).
2. **The blend?** No: the list without the blend (w = 0) had no Marvel either.
3. **Dead ReLUs / learning rate too high?** No: about 25% of hidden units stay active, only 1% of test users
   end with pick scores below 1.0, and at learning rates 0.05, 0.01 and 0.005 the Marvel pick scores
   stayed at 0.6, the starting value (target 5.0).
4. **The model?** No: the trained model gives real 5-star fans of these movies 3.0–3.6
   (Fight Club fans 2.9), and the movies got a normal number of training negatives (2.8–3.8 per rating).

So the model knows these movies well, but the fold-in, starting at the **average user vector**, sits in a
flat region for them and cannot move toward where their fans are. In v1 this start worked (cold start beat
popularity), so the problem only appeared with the v3 model.

## Decision

Start the fold-in from the **picks' fans**: for every movie, the average trained user vector of users who
rated it 4.0 or higher in train ("fan centroid"); the start is the mean of the picks' fan centroids.
Movies nobody liked in train fall back to the average user. The fold-in then runs as before
(100 Adam steps, lr 0.05, 20 popularity-sampled negatives, L2 1e-3), followed by the blend (ADR 0005).

## Measured

Hand-made users (pick score = mean model score of the 5 picks after fold-in):

| User | Average-user start | Fan start |
|---|---|---|
| Marvel fan | 0.6 · cult hits 1998–2006 | **4.36** · Infinity War Part I, Spider-Man, Deadpool, Guardians 2, Doctor Strange |
| Horror fan | no horror except 28 Days Later | **4.33** · The Witch, Autopsy of Jane Doe, Insidious, It Follows, It |
| Romance fan | Love Actually, Bridget Jones, Moulin Rouge | **3.46** · acclaimed dramas (King's Speech, The Help, Love Actually) |

Hit@10 with blend w = 4 (5 top-rated train movies as picks):

| | Val (1,000 users) | Test (1,000 users) | Different movies in test top 10s | Median rating count |
|---|---|---|---|---|
| Popularity | 0.200 | 0.211 | 132 | 66,650 |
| Average-user start | 0.199 | 0.226 | 596 | 37,916 |
| **Fan start** | **0.232** | **0.224** | **997** | **30,524** |

The val gain (+0.033) did **not** hold on test (0.224 vs 0.226, inside the ±0.013 noise). So accuracy is
unchanged. The win is variety (+67% different movies, less blockbuster-heavy) and lists that fit the picks.

## Alternatives

- **Keep the average-user start:** same test Hit@10, but generic lists and visible failures (Marvel fan).
- **Use the fan centroid directly, without fold-in:** not tried; the fold-in still adapts the start to the
  exact pick combination and keeps the match % (ADR 0003) based on fitted pick scores.
- **Tune the fold-in (more steps, other learning rates):** tried; pick scores did not move from 0.6.

## Consequences

- New artifact: fan centroids, 23,344 × 32 floats (about 3 MB), written by the training notebook from
  `train` ratings ≥ 4.0 and the trained user embeddings.
- Backend (step 7): load it in `repositories/`, add a `start` argument to `fold_in_user_vector`, a unit test
  that the start is the mean of the picks' centroids (with the average-user fallback), and keep the
  same-picks-same-result test (F4).
- Evaluation caveat: a test user's own trained vector is part of the fan centroids of movies they liked; a
  real app user is new, so this cannot happen in the app. The effect is tiny (picks have a median of about
  27k ratings each), but it slightly favours fan start in these numbers.
- The report should state both results: accuracy unchanged on test, variety and list quality better.
