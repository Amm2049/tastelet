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
notebooks/                 # Phases 1–5 in Colab; explore here first
ml/                        # tested training code graduated from notebooks
results/                   # results.csv + figures for the report
backend/
  app/
    api/           # FastAPI routes: thin — validate, call a service, return schema
    schemas/       # Pydantic request/response models
    services/      # logic: recommender (fold-in + ranking), persona, genre sentence
    repositories/  # loads artifacts / movie metadata; the only code touching files
    ml/            # NCF model class (shared by training and serving)
    core/          # config (pydantic-settings), logging, startup wiring
    main.py        # app factory, lifespan, CORS
  artifacts/       # ncf_model.pt, centroids.json, personas.json, movies_meta.json (committed)
  tests/
frontend/          # Vite + React (remove .gitkeep before `npm create vite`)
docs/              # spec, plan, proposal PDFs
  adr/             # architecture decision records
docs/devlog.md     # short note per session
```
Layer rule: api → services → repositories. Never skip a layer or import upward.

## Fixed technical decisions (from the spec — don't change without an ADR)
- MovieLens ml-latest-small; IDs re-indexed 0..N-1; 80/10/10 split.
- Random seed **42** everywhere (numpy, torch, sklearn, K-means, fold-in negative sampling).
- NCF in PyTorch: embeddings dim 32 → concat → MLP 64 → 32 → 1, ReLU, dropout 0.2; MSE, Adam (lr 1e-2).
- Two NCF models (ADR 0001): rating model (real ratings) for RMSE; ranking model
  (+4 sampled negatives per rating, label 0.5) for Hit@10 and serving as `ncf_model.pt`.
- Cold start: freeze weights, optimize one user vector (~100 steps), picks = 5.0, plus random negatives.
- Personas: K-means (K 6–12, ~8) on L2-normalized user embeddings; nearest centroid at runtime.
- Endpoints: `GET /movies`, `POST /recommend` (`movie_ids`: 5–10 ints), `GET /health`.
  Bad input → 422 with a plain message.
- TMDB data is fetched **offline** into `movies_meta.json`; the running app calls no external API.
- Artifacts loaded **once** at startup (FastAPI lifespan). Response < 3 s on CPU.
- Same picks → same persona and list (deterministic).
- Privacy: picks are never stored or logged.

## Engineering rules
- **Types:** Python type hints everywhere (checked by mypy); React with clear prop shapes
  (TypeScript preferred if Billy agrees — decide in an ADR before Phase 7).
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
- Frontend: Vitest for logic (pick limits), Playwright later for the full flow.
- Model quality: `results.csv` must show NCF beating popularity on RMSE (vs movie-mean 0.9505)
  and Hit@10.

## Definition of done (per step/issue)
- [ ] Acceptance criteria / phase done-when check met
- [ ] Tests written and passing; lint + type check clean
- [ ] No debug prints, secrets, or untracked TODOs
- [ ] README / ADR / devlog updated if relevant
- [ ] Billy has reviewed it and can explain it

## Commands
_Add as they become real (e.g. `make dev`, `make test`, `uvicorn app.main:app --reload`)._
