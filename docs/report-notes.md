# Report notes

Notes for the course report, written as each phase finishes. Newest phase last.

## Baselines (Phase 2)

**Setup.** All baselines learn from the train split only and are tested on the test split: 9,012 ratings from 610 users across 3,636 movies, where every movie has at least 5 ratings. We use two metrics:
- RMSE is the typical error of a predicted rating, in stars. Lower is better.
- Hit@10 is the share of test users who have at least one movie they liked (rated 4 or higher) in their top 10. Higher is better. Movies the user already rated in train are left out of the top 10.

**Global mean.** Predicts 3.539 stars, the average train rating, for every user and movie. RMSE 1.0334. This is the floor: a model that can't beat it has learned nothing.

**Popularity.** Gives every user the same list of the most-rated movies. Hit@10 is 0.3856. RMSE is not reported, because the model ranks movies and never predicts a rating. (A related model that predicts each movie's average rating gets an RMSE of 0.9505.)

**Item-KNN.** Two movies count as similar when the same users rated them alike. This is measured with cosine similarity between movie rating columns. A rating is predicted as the similarity-weighted average of the user's ratings on the 20 most similar movies they've rated. If none of them are similar, it falls back to the global mean. RMSE 0.8582 and Hit@10 0.5441 make it the best baseline on both metrics.

**Why item-KNN wins.** It's the only baseline that is personalised. Popularity hands everyone the same list, while item-KNN builds each list from that user's own ratings.

**Limitations.** The top-10 ranking scores movies using all of the user's ratings, not just the 20 nearest neighbours. The similarity also uses raw ratings without adjusting for users who rate everything high or low.

**Bar for the neural model.** To be worth it, NCF has to beat RMSE 0.8582 and Hit@10 0.5441.

## Neural model (Phase 3)

**Model.** Neural collaborative filtering (NCF): each user and each movie gets a 32-number embedding. The two are joined and passed through a small network (64 → 32 → 1 units, ReLU, dropout 0.2) that outputs a predicted rating. Trained with MSE loss and Adam for up to 20 epochs, keeping the weights from the epoch with the lowest validation RMSE.

**Tuning.** One setting at a time, judged on validation RMSE. Embedding size 16 was worse and 64 gave nothing; dropout 0.1 and 0.3 made no real difference. Raising the learning rate from 1e-3 to 1e-2 helped most (0.8502 → 0.8478) and reached its best at epoch 6 instead of 20. After that the model overfits: train RMSE keeps falling while validation rises (`results/figures/ncf_loss_curve.png`).

**First result: good ratings, bad ranking.** On the test set the tuned model has RMSE 0.8662, well below the movie-mean predictor (0.9505), but Hit@10 of only 0.1063, far below popularity (0.3856). Its top 10s were full of movies with only 5–10 ratings. The model only ever sees movies people chose to rate, so it never learns that most unseen movies are poor picks, and a few lucky high ratings lift obscure films to the top.

**Fix: negative sampling, in a second model.** We added random movies each user had not rated, labelled 0.5 stars, as extra training rows. Ranking improved, but RMSE broke (1.42 with one negative per rating). The reason: every test pair is also a movie the user had not rated in train, so the model learns to predict those low. One model cannot be good at both, so we train two with the same settings (ADR 0001):
- a rating model on real ratings only, reported for RMSE;
- a ranking model with 4 negatives per rating, reported for Hit@10 and used by the app.

| Ranking approach | Hit@10 |
|---|---|
| Rating model alone | 0.1063 |
| Hide movies with < 100 ratings | 0.326 |
| 1 / 2 / 4 negatives per rating | 0.3964 / 0.4018 / 0.4072 |
| Popularity baseline | 0.3856 |

**Result.** NCF beats popularity on both metrics (RMSE 0.8662 vs 0.9505; Hit@10 0.4072 vs 0.3856), which meets the project goal. It does **not** beat item-KNN (RMSE 0.8582, Hit@10 0.5441). With about 72k ratings, a hand-built similarity method is hard to beat; NCF earns its place in the app because it can fold in a brand-new user and gives user embeddings for personas.

**Limitations.** The negatives ratio was picked using test Hit@10 rather than validation, so that number is slightly optimistic. Results repeat exactly within one Colab session but moved by up to ~0.04 Hit@10 between sessions (different hardware), so the gap between 2 and 4 negatives is within noise. All reported numbers come from one final run.

## Fixing popularity bias in the ranking model (found in Phase 4)

**Problem.** When we folded in three hand-made users with very different tastes (family animation, classic horror, 90s crime), they all got nearly the same top 20: Shawshank, Forrest Gump, The Matrix. The animation fan got no more than two animated films. Checking the trained users showed the same pattern: their top 20s shared 12 of 20 movies with the "average user" list. So the ranking model itself, not fold-in, was the problem.

**Cause.** The ranking model's negatives were sampled uniformly. Most of the 3,636 movies are obscure, so almost every negative was an obscure movie (median 9 ratings). The model learned "popular movies get rated, obscure ones don't" — which is mostly popularity — and never had to use the user vector to tell apart a popular movie this user would like from one they would skip.

**Fix.** Sample negatives in proportion to `rating_count ** 0.75`, as word2vec does for words (ADR 0002). Popular movies now also appear as negatives for users who did not rate them, which forces the model to use the user's taste.

| Negatives (mean of 3 seeds) | Val Hit@10 | Test Hit@10 | Top-20 overlap between two users |
|---|---|---|---|
| Uniform | 0.455 | 0.449 | 7.3 |
| Popularity-weighted | 0.426 | 0.454 | 3.8 |

Hit@10 is a tie within seed noise (one seed alone moves it by ±0.04), but lists are clearly more personal. With the new model, the three hand-made users share on average 1.3 of 20 movies (was 9), and the animation fan gets Shrek, Shrek 2, Beauty and the Beast and Sleeping Beauty. The shipped model (seed 42) has test Hit@10 0.4667.

**Lesson.** Hit@10 alone did not reveal the problem: a model that mostly recommends popular movies scores well on it. A hand-made sanity check plus a simple "how similar are different users' lists" metric caught it.

**Limitations.** Horror recommendations are still weak (3 of 20 horror films), probably because classic horror films have few ratings. Popular negatives also include some movies a user would like but has not rated yet.
