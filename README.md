# Tastelet

Pick 5–10 movies you love; a neural network gives you a taste persona, a favourite-genre sentence and
20 recommendations with match scores.

AI course term project (Rangsit University): neural collaborative filtering (NCF) on MovieLens,
cold-start fold-in for new users, and K-means personas.

## Quick start (local)

Needs Python 3.10 and Node 22.

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r backend/requirements-dev.txt   # macOS/Linux: .venv/bin/python
cd backend && ../.venv/Scripts/python -m uvicorn app.main:app --reload                         # API on http://localhost:8000
cd frontend && npm install && npm run dev                                                      # app on http://localhost:5173 (2nd terminal)
```

Checks: `cd backend && ../.venv/Scripts/python -m pytest` and `cd frontend && npm test`.

## How it works

```
React (Vite) ──POST /recommend──▶ FastAPI ── 1 fold in the new user (frozen NCF, 100 Adam steps)
     ▲                                     ── 2 score all movies (+ small "prefer newer" boost),
     │                                          drop the picks, keep the top 20
     └──── persona + rows ◀─────────────── ── 3 nearest K-means centroid → persona
                                           ── 4 genre sentence, franchise row, genre rows
                                 artifacts/ (model + JSON, loaded once at startup)
```

The picker shows Netflix-style rows (recent hits first, one row per genre, Japanese animation) and a
title search. The results page shows the #1 match as a banner, then "Top picks for you" (the model's
own ranking), "More from your franchises" and "Because you love <genre>" rows.

Training is offline in `notebooks/` (Colab or local); its outputs live in `backend/artifacts/`.

| Model (test set) | RMSE | Hit@10 |
|---|---|---|
| Global mean | 1.0334 | – |
| Popularity | – | 0.3856 |
| Item-KNN | **0.8582** | **0.5441** |
| NCF rating model | 0.8662 | 0.1063 |
| NCF ranking model (shipped) | – | 0.4667 |
| NCF cold start, 5 picks (100 users) | – | 0.41 (popularity 0.36) |

NCF beats popularity on both metrics but not item-KNN; it is used because it can fold in a brand-new
user and gives the user vectors the personas are built from. Details: `docs/report-notes.md` and the
decision records in `docs/adr/`.

## API

| Endpoint | Request | Response |
|---|---|---|
| `GET /movies` | – | `{rows: [{key, title, movies}]}`: picker rows; movies have `id, title, year, genres, poster` |
| `GET /movies/search?q=` | text (2+ characters) | `{movies: [...]}`: up to 20 title matches, most rated first |
| `POST /recommend` | `{"movie_ids": [...]}`, 5–10 unique ids | `{persona, description, genre_sentence, recommendations, franchise_row, genre_rows}`; movies have `id, title, year, genres, overview, poster, score` |
| `GET /health` | – | `{"status": "ok"}` |

Bad input returns `422` with one plain sentence in `detail`. Interactive docs: `/docs`.

## Deploy (free tiers)

1. **Backend on Render:** Dashboard → New → Blueprint → this repo (uses `render.yaml`). When asked for
   `ALLOWED_ORIGINS`, enter a placeholder for now. Wait for "Live", then open `<render-url>/health`.
2. **Frontend on Vercel:** New Project → this repo → Root Directory `frontend` (Vite preset) →
   environment variable `VITE_API_URL=<render-url>` → Deploy.
3. **Connect them:** in Render, set `ALLOWED_ORIGINS=<vercel-url>` (no trailing slash) → it redeploys.
4. Open the Vercel URL in a fresh window and run the demo below. The free backend sleeps after
   15 minutes idle; the first visit can take about a minute (the page says so).

## Demo (about 3 minutes)

1. Open the site 5 minutes early so the backend is awake.
2. Pick 5 family animations (Toy Story, The Lion King, Aladdin, Finding Nemo, Monsters, Inc.; use search)
   → **The Dreamer**. Scroll to "More from your franchises": Toy Story 2 and 3, Monsters University, …
3. Start over (top of the page) → pick 5 horror classics (The Shining, The Exorcist, Halloween, A Nightmare on Elm Street,
   The Texas Chainsaw Massacre) → **The Thrill Seeker**, a different list.
4. Point to the results table above.

## Project layout

```
notebooks/          01 data prep · 02 baselines · 03 NCF · 03b popularity negatives · 04 fold-in + personas
                    add_tmdb_details.py (language + franchise, run after 01) · eval_newer_boost.py (ADR 0004)
backend/app/        api (routes) → services (fold-in, ranking, persona, genre sentence) → repositories (files)
backend/artifacts/  ncf_model.pt, centroids.json, personas.json, movies_meta.json, … (made by notebook 04)
frontend/src/       App, components/ (MovieRow, HeroMatch, …), api.js, picks.js, useMovieSearch.js
results/            results.csv, figures/
docs/               spec, plan, proposal (PDF) · adr/ · report-notes.md · devlog.md · slides
```

## Credits

Data from [MovieLens](https://grouplens.org/datasets/movielens/) (GroupLens). This product uses the TMDB API
but is not endorsed or certified by TMDB.
