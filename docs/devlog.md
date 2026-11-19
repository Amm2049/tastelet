# Devlog

One entry per work session: yesterday / today / blockers. Newest first.

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
