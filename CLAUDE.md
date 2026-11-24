# CLAUDE.md — Tastelet

Instructions for Claude when working in this repo. Read fully before every task.

## What this project is
Tastelet: a movie recommender web app (AI course term project, built solo by Billy).
The user picks 5–10 favorite movies → the app returns a taste persona, a favorite-genre
sentence and 10–20 recommended movies with match scores. No accounts, no database.

Sources of truth: the v1 spec, plan and proposal PDFs were removed as outdated (2026-11-24); they are in git at
tag `v3.0` (`git show v3.0:docs/scope-and-specification.pdf > spec.pdf`). v3 sources: `docs/overview.md` (how it all works), README.md, `docs/adr/` (every decision since)
and `docs/devlog.md`. Slides + speaker script: `docs/slides/` (the .pptx is also imported into Canva; Canva's AI
design tools are disabled on Billy's team, so decks are built as .pptx and imported by hand).

Scope is frozen. New ideas go to a "Later" list in an issue, never into the build.

## How we work together (most important)
Billy is a final-year CS student using this project to build senior-engineer habits.
He wants to understand every part, not receive finished code.

1. **One small step at a time.** Never build a whole phase or feature in one go.
   A step = about one PR (< ~300 changed lines), ideally much smaller.
2. **Explain before coding.** For each step state: what we're building, why this design,
   alternatives considered, and which habit it practices.
3. **Then write the code**, and walk through the key lines afterwards.
4. **Stop and let Billy review.** Wait for his go-ahead before the next step.
   Point out what a reviewer would question.
5. **Make him active.** Sometimes ask him to write a small part, predict an output,
   or explain a piece back. Don't do this every step — about once per session.
6. **Never hide complexity.** If something is tricky (tensor shapes, fold-in math, CORS),
   explain it plainly. Never commit code he can't explain.
7. Remind him of the workflow (issue, branch, commit message, PR) at the right moment,
   and propose the exact commit message.

## Repo layout
```
data/raw, data/processed   # MovieLens + TMDB cache (git-ignored)
notebooks/                 # Phases 1–5 (training + evaluation); 04 also exports backend artifacts
results/                   # results.csv + figures for the report
backend/
  app/
    api/           # FastAPI routes: thin — validate, call a service, return schema
    schemas/       # Pydantic request/response models
    services/      # logic: recommender (fold-in + ranking), persona, genre sentence,
                   # v2: browse (picker rows), search, titles, result_rows (franchise + genre rows)
    repositories/  # loads artifacts / movie metadata; the only code touching files
    ml/            # NCF model class (shared by training and serving)
    core/          # config.py: constants + ALLOWED_ORIGINS from the environment
    main.py        # app factory, lifespan, CORS
  artifacts/       # ncf_model.pt, centroids.json, personas.json, movies_meta.json, movie2idx.json,
                   # movie_rating_counts.json (committed; written by notebook 04)
  tests/           # pytest: unit + FastAPI TestClient
frontend/          # Vite + React (JavaScript); src/components, api.js, picks.js; Vitest
docs/              # overview.md (how it all works), slides/ (deck, speaker script, screenshots)
  adr/             # architecture decision records
docs/devlog.md     # short note per session
render.yaml        # Render blueprint for the backend (frontend goes on Vercel)
```
Layer rule: api → services → repositories. Never skip a layer or import upward.

## Fixed technical decisions (from the spec — don't change without an ADR)
- MovieLens ml-latest-small; IDs re-indexed 0..N-1; 80/10/10 split. **v3:** ml-32m, per-user time split (see v3 below).
- Random seed **42** everywhere (numpy, torch, sklearn, K-means, fold-in negative sampling).
- NCF in PyTorch: embeddings dim 32 → concat → MLP 64 → 32 → 1, ReLU, dropout 0.2; MSE, Adam (lr 1e-2).
- Two NCF models (ADR 0001): rating model (real ratings) for RMSE; ranking model
  (+4 sampled negatives per rating, label 0.5) for Hit@10 and serving as `ncf_model.pt`.
  Negatives sampled ∝ rating_count^0.75 in training and fold-in (ADR 0002).
- Cold start: freeze weights, optimize one user vector (~100 steps), picks = 5.0, plus random negatives.
  **v3:** starts from the picks' fan centroids, not the average user (ADR 0006).
- Personas: K-means on L2-normalized user embeddings, **K = 6** (genres ranked by lift, not counts;
  no look-alike clusters at K = 6); nearest normalized centroid (cosine) at runtime. **v3: K = 7** (ADR 0007).
- Match score = score / best pick score, clipped 0–100 (ADR 0003), not the plan's score / 5.
- Fold-in is warmed up once at startup so the first user's request is fast.
- Endpoints: `GET /movies` (picker rows), `GET /movies/search?q=` (v2), `POST /recommend`
  (`movie_ids`: 5–10 ints), `GET /health`. Bad input → 422 with a plain message.
- TMDB data is fetched **offline** into `movies_meta.json`; the running app calls no external API.
  Notebook 01 writes the file; then `notebooks/add_tmdb_details.py` adds `original_language` and the
  TMDB franchise (`collection_id`, `collection_name`). Re-running notebook 01 drops those, so always
  run the script after it.

## v2 (picker + results page; merged into `main` with v3 and live since 2026-11-24, PR #25)
- Why: results felt "too old" because the v1 picker only offered old movies (see ADR 0004).
- Picker rows (`services/browse.py`): Recent hits (2010+), one row per genre in `BROWSE_GENRES`
  (2000+, 2010s first), Japanese animation right after Animation (and kept out of it). Each movie
  appears once per page; the first row wins. Plus title search and a "Your picks" row.
- Ranking: "prefer newer" boost `NEWER_BOOST = 0.3` (ADR 0004); Hit@10 unchanged.
- Results page: Start over at the top, persona + genre sentence (keep it), hero = #1 match,
  "Top picks for you" = rest of the top 20. The main list is always the model's own ranking.
  Then "More from your franchises" (unpicked movies of the picks' TMDB franchises, may repeat a
  top pick on purpose), then "Because you love <genre>" rows with a fun caption (never repeat a movie).
- Titles are shown as "The Dark Knight", not MovieLens's "Dark Knight, The" (`services/titles.py`).
- Theme: dark with a vibrant red accent; every colour is a token at the top of `frontend/src/index.css`.
- `uvicorn --reload` hangs on Windows here; restart the backend by hand.

## v3 (live since 2026-11-24, PR #25, tag `v3.0`; work in `D:\RSU\AI\tastelet` on `main`, the v2/v3 worktrees are gone)
- Why: v1/v2 movies end in 2018; v3 retrains on MovieLens **ml-32m** (movies to 2023) on Colab (T4 GPU).
- Data: movies with ≥ 20 ratings (23,344 movies, 200,948 users); **per-user time split** 80/10/10 (each
  user's oldest ratings train, newest test). Ranking model only (no rating model, no RMSE in v3).
- Results (1,000 test users, 5 picks): popularity 0.211 · v3 cold start **0.224** with 997 different movies
  in their top 10s vs popularity's 132. Full history 0.2162 vs popularity 0.1934 (5,000 users).
- Cold start = fan start (ADR 0006) + popularity blend `BLEND_W = 4` (ADR 0005) + newer boost (to 2023).
  Always check list **variety** and real hand-made lists, not only Hit@10 (it hid both problems).
- Movies without a poster or year (339) stay in the model but are **hidden** (`hidden_idxs`) from picker,
  search, results and franchise rows.
- Notebooks: Colab `v3_01_explore`, `v3_02_train` (GPU), `v3_03_personas` (CPU). TMDB metadata:
  `notebooks/build_movies_meta_v3.py` (one request per movie; inputs in git-ignored `data/processed_v3/`).
- MovieLens titles can differ from today's: Avengers: Endgame is "Avengers: Infinity War - Part II".
- Picker rows rank by **ratings per year since release** (`RATINGS_LAST_YEAR = 2023`), or almost no 2020+
  movie made a row (they had little time to collect ratings).
- New releases not in MovieLens can't be added: NCF has no vector for a movie without ratings (item cold
  start). A content-based model would be needed; it's future work, not in scope.
- Memory: peak ~401 MB locally (v1 293 MB) vs Render free 512 MB. If Render runs out, stop keeping the 200k
  user vectors after load (serving only needs movie vectors, centroids and fan centroids).

- Artifacts loaded **once** at startup (FastAPI lifespan). Response < 3 s on CPU.
- Same picks → same persona and list (deterministic).
- Privacy: picks are never stored or logged.

## Engineering rules
- **Types:** Python type hints everywhere (mypy strict); frontend is plain JavaScript (Billy's choice,
  2026-11-19), so keep props few and obvious.
- **Names say intent:** `fold_in_user_vector`, `is_valid_pick_count`; no `data`, `tmp`, `process`.
- **Small functions** (~30 lines max), one job each. No magic numbers — constants in `core/config.py`.
- **Errors at the edges:** Pydantic validates in routes; services raise clear domain errors
  (`UnknownMovieError`); no bare `except:`.
- **Pure functions** for data steps and genre sentence so they're easy to test.
- **Comments explain why**, not what. No dead or commented-out code.
- **No premature abstraction:** extract on the third repetition.
- **Format/lint:** Ruff (format + lint) and mypy for Python; Prettier + ESLint for frontend.

## Workflow
- Every change: GitHub issue → branch → small commits → PR → self-review → CI green → squash merge.
- Branches: `feat/<issue>-short-name`, `fix/...`, `chore/...`, `docs/...`.
- Conventional Commits: `feat(api): add /recommend endpoint`, `test(ml): cover hit_at_10`,
  `refactor(services): extract persona assignment`. Each commit builds and passes tests.
- Never push to `main` directly. Never mix a refactor and a feature in one PR.
- Big decisions → `docs/adr/NNNN-title.md` (Context, Decision, Alternatives, Consequences).

## Testing
- Bug fix → write the failing test first.
- Unit tests (pytest) for: evaluation helpers, genre sentence, persona assignment, ranking
  (no picks in output, 10–20 results, deterministic).
- Integration tests with FastAPI `TestClient` for all three endpoints, including 422 cases.
- Frontend: Vitest for pick rules (`picks.test.js`) and the full flow with a mocked API (`App.test.jsx`).
- Model quality: `results.csv` must show NCF beating popularity on RMSE (vs movie-mean 0.9505)
  and Hit@10.

## Definition of done (per step/issue)
- [ ] Acceptance criteria / phase done-when check met
- [ ] Tests written and passing; lint + type check clean
- [ ] No debug prints, secrets, or untracked TODOs
- [ ] README / ADR / devlog updated if relevant
- [ ] Billy has reviewed it and can explain it

## Commands
- Install (backend): `.venv/Scripts/python -m pip install -r backend/requirements-dev.txt`
- Tests: `cd backend && ../.venv/Scripts/python -m pytest`
- Lint + types: `cd backend && ../.venv/Scripts/python -m ruff format . && ../.venv/Scripts/python -m ruff check . && ../.venv/Scripts/python -m mypy app tests`
- Run API: `cd backend && ../.venv/Scripts/python -m uvicorn app.main:app --reload` (docs at http://localhost:8000/docs)
- Frontend: `cd frontend && npm install && npm run dev` (http://localhost:5173)
- Frontend checks: `cd frontend && npm run format:check && npm run lint && npm test && npm run build`
- CI (`.github/workflows/ci.yml`) runs all backend and frontend checks on every PR.
