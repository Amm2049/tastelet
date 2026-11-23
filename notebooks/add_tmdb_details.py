"""Offline step (v2): add TMDB details to backend/artifacts/movies_meta.json.

Adds to every movie:
- original_language: for the "Japanese animation" picker row (MovieLens has no country or language field).
- collection_id, collection_name: the TMDB franchise ("Toy Story Collection"), for the
  "More from your franchises" results row; null when the movie is not part of one.

Like the posters (notebook 01), this runs once offline; the running app calls no external API.

Run from the repo root:  python notebooks/add_tmdb_details.py <path to links.csv> <path to .env>
Answers are cached in data/raw/tmdb_details_cache.json, so a re-run only fetches what is missing.
"""

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

META_PATH = Path("backend/artifacts/movies_meta.json")
CACHE_PATH = Path("data/raw/tmdb_details_cache.json")
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}?"
NOT_ON_TMDB: dict[str, Any] = {"original_language": "", "collection_id": None, "collection_name": None}
WORKERS = 8  # parallel requests; TMDB allows ~50 per second
BATCH_SIZE = 200  # save the cache after each batch, so an interruption loses little
MAX_ATTEMPTS = 4
RETRY_WAIT_SECONDS = 2.0


def read_api_key(env_path: Path) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "TMDB_API_KEY" and value.strip():
            return value.strip()
    sys.exit(f"TMDB_API_KEY not found in {env_path}")


def details_from(tmdb_movie: dict[str, Any]) -> dict[str, Any]:
    collection = tmdb_movie.get("belongs_to_collection") or {}
    return {
        "original_language": tmdb_movie.get("original_language") or "",
        "collection_id": collection.get("id"),
        "collection_name": collection.get("name"),
    }


def fetch_details(tmdb_id: str, api_key: str) -> dict[str, Any]:
    url = TMDB_MOVIE_URL.format(tmdb_id=tmdb_id) + urllib.parse.urlencode({"api_key": api_key})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return details_from(json.load(response))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return NOT_ON_TMDB
            if error.code != 429 or attempt == MAX_ATTEMPTS:  # 429 = rate limited: wait and retry
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == MAX_ATTEMPTS:  # a dropped connection is usually temporary
                raise
        time.sleep(RETRY_WAIT_SECONDS * attempt)
    raise AssertionError("unreachable")


def fill_cache(tmdb_ids: list[str], api_key: str, cache: dict[str, Any]) -> None:
    missing = sorted({tmdb_id for tmdb_id in tmdb_ids if tmdb_id not in cache})
    print(f"{len(tmdb_ids)} movies, {len(missing)} to fetch")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for start in range(0, len(missing), BATCH_SIZE):
            batch = missing[start : start + BATCH_SIZE]
            cache.update(zip(batch, pool.map(lambda tmdb_id: fetch_details(tmdb_id, api_key), batch), strict=True))
            CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {min(start + BATCH_SIZE, len(missing))}/{len(missing)}")


def main(links_path: Path, env_path: Path) -> None:
    with links_path.open(encoding="utf-8") as file:
        tmdb_id_by_movie_id = {int(row["movieId"]): row["tmdbId"] for row in csv.DictReader(file)}
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    cache: dict[str, Any] = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}

    fill_cache([tmdb_id_by_movie_id[movie["id"]] for movie in meta["movies"]], read_api_key(env_path), cache)
    for movie in meta["movies"]:
        movie.update(cache[tmdb_id_by_movie_id[movie["id"]]])
    META_PATH.write_text(json.dumps(meta), encoding="utf-8")

    in_collections = [movie for movie in meta["movies"] if movie["collection_id"] is not None]
    print(f"saved; {len(in_collections)} movies in {len({m['collection_id'] for m in in_collections})} franchises")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
