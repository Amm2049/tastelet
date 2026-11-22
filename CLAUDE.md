# CLAUDE.md — Tastelet

Instructions for Claude when working in this repo. Read fully before every task.

## What this project is
Tastelet: a movie recommender web app (AI course term project, built solo by Billy).
The user picks 5–10 favorite movies → the app returns a taste persona, a favorite-genre
sentence and 10–20 recommended movies with match scores. No accounts, no database.

Sources of truth (in `docs/`):
- `docs/scope-and-specification.pdf` — features F1–F6, API, non-functional requirements
- `docs/implementation-plan.pdf` — setup + Phases 1–9, done-when checks
- `docs/project-proposal.pdf` — proposal deck

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
docs/              # spec, plan, proposal PDFs; slides
  adr/             # architecture decision records
docs/devlog.md     # short note per session
render.yaml        # Render blueprint for the backend (frontend goes on Vercel)
```
Layer rule: api → services → repositories. Never skip a layer or import upward.

## Fixed technical decisions (from the spec — don't change without an ADR)
- MovieLens ml-latest-small; IDs re-indexed 0..N-1; 80/10/10 split.
- Random seed **42** everywhere (numpy, torch, sklearn, K-means, fold-in negative sampling).
- NCF in PyTorch: embeddings dim 32 → concat → MLP 64 → 32 → 1, ReLU, dropout 0.2; MSE, Adam (lr 1e-2).
- Two NCF models (ADR 0001): rating model (real ratings) for RMSE; ranking model
  (+4 sampled negatives per rating, label 0.5) for Hit@10 and serving as `ncf_model.pt`.
  Negatives sampled ∝ rating_count^0.75 in training and fold-in (ADR 0002).
- Cold start: freeze weights, optimize one user vector (~100 steps), picks = 5.0, plus random negatives.
- Personas: K-means on L2-normalized user embeddings, **K = 6** (genres ranked by lift, not counts;
  no look-alike clusters at K = 6); nearest normalized centroid (cosine) at runtime.
- Match score = score / best pick score, clipped 0–100 (ADR 0003), not the plan's score / 5.
- Fold-in is warmed up once at startup so the first user's request is fast.
- Endpoints: `GET /movies` (picker rows), `GET /movies/search?q=` (v2), `POST /recommend`
  (`movie_ids`: 5–10 ints), `GET /health`. Bad input → 422 with a plain message.
- TMDB data is fetched **offline** into `movies_meta.json`; the running app calls no external API.
  Notebook 01 writes the file; then `notebooks/add_tmdb_details.py` adds `original_language` and the
  TMDB franchise (`collection_id`, `collection_name`). Re-running notebook 01 drops those, so always
  run the script after it.

## v2 (branch `v2`, worktree `D:\RSU\AI\tastelet-v2`; local only, not pushed or deployed)
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
- Run v2 beside v1: backend on 8001 (`ALLOWED_ORIGINS=http://localhost:5174`), frontend on 5174
  (`VITE_API_URL=http://localhost:8001`). `uvicorn --reload` hangs on Windows here; restart by hand.
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
