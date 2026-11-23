# 0007. Seven personas (K = 7) for the v3 model

- Status: accepted
- Date: 2026-11-23
- Context of v3: model retrained on MovieLens `ml-32m` (branch `v3`, not deployed); replaces K = 6 from
  the fixed decisions in CLAUDE.md for v3 only

## Context

v1 chose K = 6 because, with genres ranked by lift, no two clusters shared 2 of their top 3 genres.
We re-ran the same check on the v3 user vectors (200,948 users, L2-normalized, K-means `random_state=42`,
`n_init=10`; Colab notebook `v3_03_personas`, CPU):

| K | Look-alike pairs | Smallest cluster | Marvel / horror / romance hand-made users land in |
|---|---|---|---|
| 6 | 1 | 27,187 | 0 / 2 / 2 |
| **7** | **0** | **23,535** | **5 / 0 / 5** |
| 8 | 2 | 16,886 | 6 / 2 / 6 |
| 9 | 2 | 15,386 | 8 / 4 / 8 |
| 10 | 4 | 14,555 | 9 / 5 / 9 |

At K = 6 two clusters both had Western + Musical on top. K = 7 is the only K with no look-alikes.

## Decision

K = 7. Profiles use genre lift (as in v1) and, new in v3, the cluster's top movies ranked by **lift** too
(share of the cluster's likes / share of all likes, with at least 1,000 likes inside the cluster). Ranking
movies by like rate, as v1 did, put Shawshank and The Godfather at the top of every cluster.

| Cluster | Users | Top movies by lift | Persona |
|---|---|---|---|
| 0 | 23,535 | The Holiday, 13 Going on 30, The Proposal, Enchanted | The Rom-Com Regular |
| 1 | 25,385 | Grumpier Old Men, Phenomenon, A Time to Kill | The Comfort Watcher |
| 2 | 31,679 | Star Trek: Insurrection, Star Trek VI, Star Trek III | The Starship Captain |
| 3 | 27,968 | Atlantic City, Nashville, Klute, Diva | The Film Buff |
| 4 | 27,092 | There Will Be Blood, Oldboy, The Hunt, City of God | The Case Cracker |
| 5 | 31,411 | Avengers: Infinity War I + II, Thor: Ragnarok, Guardians 2 | The Blockbuster Hero |
| 6 | 33,878 | Disclosure, Under Siege 2, The Specialist, The Net | The Action Junkie |

Names were written from the movies (the clearer signal) and saved to `personas_v3.json`; the runtime rule is
unchanged (nearest normalized centroid by cosine).

## Alternatives

- **Keep K = 6:** one look-alike pair, and clusters were harder to describe.
- **K = 8–10:** more look-alike pairs and smaller clusters.
- **Require the three hand-made users to land in different clusters:** no K from 6 to 10 does it.

## Consequences

- **Clusters mix era with taste.** MovieLens users rated movies while they were current, so clusters 1, 3 and 6
  are mostly 1990s / 1970s–80s viewers. App users pick mostly 2000+ movies (v2 picker), so they will
  rarely get those personas; they still exist so every vector has a sensible nearest persona.
- **Known weakness:** the horror fan (Get Out, Hereditary, The Conjuring 1–2, A Quiet Place) lands in cluster 0,
  the rom-com persona; cluster 0's genre lift (Documentary, Horror, Animation) does not match its movies.
  The genre sentence under the persona comes from the picks, so the page still says "horror".
  The romance fan lands in the Blockbuster cluster because the picks are recent rather than because of genre.
  In the backend (step 7), classic animation picks (Toy Story, The Lion King, Aladdin, Finding Nemo, Monsters, Inc.)
  get The Action Junkie and classic horror picks (The Shining, The Exorcist, Halloween…) The Starship Captain,
  although their lists fit (Disney and Pixar; Ringu, Dawn of the Dead). The tests only lock in personas that fit
  (Marvel picks -> The Blockbuster Hero, 90s crime -> The Case Cracker).
- The backend reads the number of personas from the files (`unit_centroids` has shape (n_personas, dim)),
  so K = 7 needs no code change; step 7 copies `centroids_v3.json` / `personas_v3.json` into `backend/artifacts/`.
- CLAUDE.md's fixed decision "K = 6" must say "K = 6 (v1), K = 7 (v3, ADR 0007)" when v3 is merged.
