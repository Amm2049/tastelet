# Tastelet: how it works (v3)

A short map of the whole project, for reviewing it later. The *why* behind each decision is in
`docs/adr/` (linked below); the day-by-day story is in `docs/devlog.md`; how to run and deploy is in
`README.md`.

## 1. What it does

A new user picks 5–10 movies they love. The app returns a **taste persona**, a favourite-genre sentence and
**20 recommendations** with match scores, plus "More from your franchises" and "Because you love <genre>" rows.
No accounts, no database, picks are never stored. Live: https://tastelet.vercel.app

The core problem is **user cold start**: the app knows nothing about a new user except their picks.

## 2. Data

- **MovieLens ml-32m** (ratings to 2023), kept movies with ≥ 20 ratings: 23,344 movies, 200,948 users.
- **Per-user time split 80/10/10**: each user's oldest ratings train, the newest test. This copies real use
  (predict what someone likes *next*) and stops the model from peeking at the future. Harder than v1's random
  split, so the numbers are lower.
- **TMDB** posters, overviews, language and franchise, fetched **offline** into `movies_meta.json`
  (`notebooks/build_movies_meta_v3.py`). The running app calls no external API.
- 339 movies without a poster or year stay in the model but are hidden in the app.

## 3. Model: why NCF

**Neural collaborative filtering:** one learned vector (32 numbers) per user and per movie →
concatenate → MLP 64 → 32 → 1 (ReLU, dropout 0.2), trained with MSE + Adam. It is a **ranking model**:
real ratings plus 4 "negative" movies per rating (label 0.5), sampled ∝ popularity^0.75 (ADR 0001, 0002).
Trained on Colab (T4 GPU), seed 42 everywhere.

Alternatives and trade-offs:
- **Popularity** (same list for everyone): simple and hard to beat on Hit@10, but not personal. Used as the baseline.
- **Item-KNN**: beat NCF on v1's small data (Hit@10 0.54 vs 0.47), but gives no user vectors, so no personas.
- **Content-based (genres, text)**: handles brand-new movies, but only sees genres, not taste.
- **NCF** was chosen because a new user can be **folded in** without retraining, and its user vectors give the
  personas. The price: it can't recommend a movie with no ratings (item cold start).

## 4. Serving a new user (`POST /recommend`)

1. **Fold-in**: freeze the trained model and learn only a new user vector: picks = 5.0, plus 20 sampled
   negatives, 100 Adam steps. Start from the **picks' fans** (average vector of users who rated each pick
   ≥ 4), not the average user. The average start got stuck: a Marvel fan got Fight Club (ADR 0006).
2. **Rank**: model score + **popularity blend** (`BLEND_W = 4`, ADR 0005) + small **"prefer newer"** boost
   (0.3, ADR 0004). Drop the picks, keep the top 20.
3. **Match score** = score / best pick's score, clipped 0–100 (ADR 0003).
4. **Persona**: nearest of **7 K-means centroids** (cosine on L2-normalised user vectors). Clusters are
   described by genre and movie *lift*, not counts, or every cluster looks like "Drama, Comedy" (ADR 0007).
5. **Rows**: franchise row from TMDB collections; genre rows from the top 100 candidates, no repeats.

Deterministic: same picks → same persona and list (seed 42). The model loads once at startup; a request takes about 1 s.

## 5. Results (test set, 1,000 users, 5 picks each)

| | Hit@10 | Different movies in all top 10s |
|---|---|---|
| Popularity | 0.211 | 132 |
| NCF cold start (fan start + blend) | **0.224** | **997** |

With full history: NCF 0.216 vs popularity 0.193 (5,000 users). Noise is about ±0.013, so for 5 picks
the accuracy gain is small. The real win is **variety**: lists are personal, not everyone's blockbusters.

**Main lesson: Hit@10 hid two problems.** (1) From 5 picks the plain model *lost* to popularity
(0.159 vs 0.211): fixed by the blend. (2) Lists didn't fit the picks (Marvel fan → Fight Club), invisible
in Hit@10: found by looking at hand-made users, fixed by the fan start. So always check **variety** and
**real lists**, tune on val and check test **once** (the fan start's +0.033 on val did not hold on test).

## 6. System

```
React (Vite, Vercel) ──▶ FastAPI (Render free) ──▶ artifacts/ (model + JSON, loaded once)
                          api → services → repositories
```

Endpoints: `GET /movies` (picker rows), `GET /movies/search?q=`, `POST /recommend`, `GET /health`.
Bad input → 422 with a plain message. CI runs pytest, Ruff, mypy, Vitest, ESLint and Prettier on every PR.

## 7. Retraining (if ever needed)

Colab, in order: `v3_01_explore` (data + split) → `v3_02_train` (GPU: NCF, blend, fan centroids) →
`v3_03_personas` (CPU: K-means) → `build_movies_meta_v3.py` (TMDB) → copy the outputs into
`backend/artifacts/`. Check the Marvel control user: its pick score should be **4.36**.

## 8. Limits and future work

- **New releases can't be added** (item cold start): NCF has no vector for a movie without ratings.
  Future work: a content-based model (genres, overview text) for new movies.
- **Personas mix era with taste**: MovieLens users rated movies when they came out, so some clusters are
  "90s viewers". Some pick sets get an odd persona even though their list fits (ADR 0007).
- **Memory**: about 401 MB of Render's 512 MB. If it runs out, stop keeping the 200k user vectors after load.
- Free backend sleeps when idle: the first visit can take about a minute.
