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
