# Devlog

One entry per work session: yesterday / today / blockers. Newest first.

## 2026-11-24
- Yesterday: v3 steps 5–7 (evaluation, TMDB metadata, backend); committed the three Colab notebooks.
- Today: picker rows rank by ratings per year since release, so 2019–2022 movies show up. Deployed v2 + v3
  (PR #25, merge commit): live on Render + Vercel, Marvel picks -> The Blockbuster Hero in 0.85 s. Removed the
  v2/v3 worktrees; tagged v3.0.
- Learned: measure memory before deploying to a small server (v3 peaks at ~401 MB of Render's 512 MB).
- Blockers: none. Next: presentation slides.

## 2026-11-23
- Yesterday: v3 steps 1–4 on Colab (ml-32m, MIN_RATINGS 20, per-user time split, GPU training; val Hit@10 0.2442).
- Today: v3 step 5 evaluation. Test Hit@10 NCF 0.2162 vs popularity 0.1934. Cold start (5 picks) lost to
  popularity (0.159 vs 0.211); ruled out fold-in settings, pick choice and the newer boost one by one.
  Fix: blend scaled popularity into the cold-start score, w = 4 chosen on val + list variety (ADR 0005):
  test 0.226, 596 different movies vs popularity's 132.
- Then: hand-made lists were wrong (Marvel fan got Fight Club). Ruled out split, blend, dead ReLUs and the
  model itself; cause = fold-in starting at the average user can't move. Fix: start from the picks' fans
  (ADR 0006): Marvel fan gets Marvel; test Hit@10 unchanged (0.224), variety 596 -> 997 movies.
- Learned: a measurable symptom (low pick scores) is not always the cause; Hit@10 can be won by giving
  everyone the popular list, so always check variety too; tune on val, test once (the fan-start val gain
  of +0.033 did not hold on test); look at real lists, they caught what Hit@10 hid.
- Then: K = 7 personas (ADR 0007; clusters mix era and taste). Step 6: one-pass TMDB metadata for 23,344 movies
  (321 without poster, 18 without year: hidden in the app). Step 7: backend serves v3 (hidden movies,
  fan start, popularity blend); 83 tests; backend reproduces the notebook's Marvel pick score (4.36) exactly.
- Learned: control checks (a known number that must repeat) caught nothing wrong today, which is the point:
  every new measurement was trusted because its control matched.
- Blockers: Colab notebooks `v3_01_explore`, `v3_02_train`, `v3_03_personas` are not in the repo yet;
  real-app check in the browser still to do.

## 2026-11-22
- Today: started v2 in a git worktree (`tastelet-v2`, branch `v2`, local only). Billy found "too many old
  movies" in the results. Reproduced with three pick sets: the model follows the picks' era. Real cause:
  the v1 picker offered mostly old movies ("Trending this week" matched 0 movies and fell back to
  "Most popular", i.e. 90s classics).
- Built Netflix-style rows: picker (Recent hits, genre rows with 2010s first, Japanese animation, search)
  and results (hero, Top picks, "More from your franchises", captioned genre rows, Start over at the top).
  TMDB language and franchise data fetched offline by `notebooks/add_tmdb_details.py`.
- Added a "prefer newer" boost (0.3). Measured with `notebooks/eval_newer_boost.py`: Hit@10 unchanged
  (0.4667 warm, 0.41 cold start); share of 2010+ results only 7% → 8% (ADR 0004).
- Learned: reproduce a bug before fixing it; the problem was in the input, not the model. Reproduce the
  old metric exactly before trusting a new one. Check every commit on its own, not just the last.
- Blockers: no movies after 2018 without retraining on `ml-32m`.

## 2026-11-19
- Yesterday: away since Oct 27; deadline moved to Nov 23, so scope is trimmed (local demo, no deploy).
- Today: Phase 5 personas (#14). K-means on normalized user vectors; silhouette ~0.1 for every K, so chose by readability. Counting genres gave every cluster Drama/Comedy/Action, so genres are ranked by lift instead. K=6: no look-alike clusters (K=8 had 5 pairs). Saved `centroids.json` and `personas.json`; the three hand-made users land in The Dreamer, The Thrill Seeker and The Case Cracker.
- Learned: when metrics can't decide (flat silhouette), pick a justified default and check it by looking at the output.
- Later: Phase 6 backend (#16, PR #17): NCF loader, fold-in, ranking, personas, genre sentence and the three endpoints; 30 pytest tests, ruff + mypy strict, CI. Phase 7 frontend (#18, PR #19): React (JavaScript) grid, picker, result page; 19 Vitest tests; checked in real Chrome at 1280 px and 360 px.
- Found in the browser: the first request took 7 s (PyTorch warm-up) -> warm up at startup; rows of "100% match" -> match relative to the best pick (ADR 0003).
- Learned: test in the real app, not only with unit tests; both bugs were invisible to the test suite.
- Blockers: deploy needs Billy's Render and Vercel accounts (steps in README).

## 2026-10-27
- Today: opened Phase 4 (#10); `score_vec`, `fold_in`, `recommend` in notebook 04. Hand-made users got near-identical generic lists. Diagnosed: the ranking model mostly scores by popularity (uniform negatives are obscure movies). Opened #11: popularity-weighted negatives; personal lists, Hit@10 unchanged within seed noise (ADR 0002). Training now runs locally in `.venv`.
- Learned: measure before fixing (model vs fold-in test pointed to the real cause); Hit@10 can hide popularity bias; compare models over several seeds before trusting a 0.05 difference.
- Later: Phase 4 notebook 04 runs locally with the new model: hand-made users get different, fitting lists; cold-start Hit@10 (5 picks) 0.41 vs popularity 0.36 on the same 100 users. The plan's match score (pred / 5) works with the new model.
- Blockers: none; Phase 5 next.

## 2026-10-24
- Yesterday: tuned NCF (lr 1e-2 best); found Hit@10 0.106, far below popularity; wrote negative sampling.
- Today: negatives fixed ranking but broke RMSE, so we now train two models (ADR 0001). Ranking model with 4 negatives: Hit@10 0.407. Phase 3 done: notebook, results.csv, loss curve, ADR, report notes.
- Learned: a notebook in the repo must pass Run all; and Colab results shift a little between sessions, so commit numbers from a single final run and compute them in code, never type them in.
- Blockers: `ncf_model.pt` is on Drive only; copy into `backend/artifacts/` in Phase 6.

## 2026-10-23
- Today: opened issue #8; Dataset, NCF model, training loop, tuning, test evaluation, negative sampling.
- Blockers: none.

## 2026-10-19
- Yesterday: popularity baseline done.
- Today: item-KNN — RMSE 0.8582, Hit@10 0.544, best baseline so far. Wrote results.csv and committed the notebook.
- Learned: item-KNN should average over the 20 most similar movies only (as the plan says), not every rated movie; weak neighbours add noise. Check the plan before coding a step.
- Blockers: none.

## 2026-10-18
- Today: ran popularity baseline — RMSE 0.9505 (beats global mean 1.0334), Hit@10 0.386.
- Blockers: notebook still only in Colab, not in the repo yet.

## 2026-10-17
- Yesterday: missed Phase 2 dates; rescheduled, end date moved to Nov 5.
- Today: opened issue #5 and branch `feat/5-baselines`; wrote the `rmse` helper and checked it on a fake model (1.0).
- Blockers: busy until Oct 21, so only small steps until then.

## 2026-10-11
- Today: created repo structure and CLAUDE.md.
- Blockers: none.
