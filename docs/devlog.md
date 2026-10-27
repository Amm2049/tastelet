# Devlog

One entry per work session: yesterday / today / blockers. Newest first.

## 2026-10-27
- Today: opened Phase 4 (#10); `score_vec`, `fold_in`, `recommend` in notebook 04. Hand-made users got near-identical generic lists. Diagnosed: the ranking model mostly scores by popularity (uniform negatives are obscure movies). Opened #11: popularity-weighted negatives; personal lists, Hit@10 unchanged within seed noise (ADR 0002). Training now runs locally in `.venv`.
- Learned: measure before fixing (model vs fold-in test pointed to the real cause); Hit@10 can hide popularity bias; compare models over several seeds before trusting a 0.05 difference.
- Blockers: Phase 4 slips to Oct 28 (shares the day with Phase 5).

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
