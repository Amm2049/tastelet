"""Offline step (v3): build movies_meta_v3.json for the ml-32m model, with TMDB details for every movie.

v1 needed two passes (notebook 01 for poster + overview, add_tmdb_details.py for language + franchise).
Here one TMDB request per movie gets all of them, plus the release year for titles without one.
Like v1, this runs once offline; the running app calls no external API.

Inputs (downloaded from Drive, git-ignored):
  data/raw/ml-32m/movies.csv, data/raw/ml-32m/links.csv
  data/processed_v3/movie2idx.json, data/processed_v3/movie_rating_counts_v3.json
Output: data/processed_v3/movies_meta_v3.json (step 7 copies it to backend/artifacts/movies_meta.json)

Run from the repo root:  python notebooks/build_movies_meta_v3.py <path to .env with TMDB_API_KEY>
Answers are cached in data/raw/tmdb_v3_cache.json, so a re-run only fetches what is missing.
"""

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

RAW_DIR = Path("data/raw/ml-32m")
PROCESSED_DIR = Path("data/processed_v3")
CACHE_PATH = Path("data/raw/tmdb_v3_cache.json")
OUTPUT_PATH = PROCESSED_DIR / "movies_meta_v3.json"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}?"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w342"  # same size as v1
NOT_ON_TMDB: dict[str, Any] = {
    "poster_path": None,
    "overview": "",
    "original_language": "",
    "collection_id": None,
    "collection_name": None,
    "release_year": None,
}
NO_GENRES = "(no genres listed)"
N_POPULAR = 20  # home_lists["popular"]: main.py warms up the fold-in with its first picks
WORKERS = 8  # parallel requests; TMDB allows ~50 per second
BATCH_SIZE = 200  # save the cache after each batch, so an interruption loses little
MAX_ATTEMPTS = 4
RETRY_WAIT_SECONDS = 2.0
TITLE_YEAR = re.compile(r"\s*\((\d{4})\)\s*$")


def read_api_key(env_path: Path) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "TMDB_API_KEY" and value.strip():
            return value.strip()
    sys.exit(f"TMDB_API_KEY not found in {env_path}")


def details_from(tmdb_movie: dict[str, Any]) -> dict[str, Any]:
    collection = tmdb_movie.get("belongs_to_collection") or {}
    release_date = tmdb_movie.get("release_date") or ""
    return {
        "poster_path": tmdb_movie.get("poster_path"),
        "overview": tmdb_movie.get("overview") or "",
        "original_language": tmdb_movie.get("original_language") or "",
        "collection_id": collection.get("id"),
        "collection_name": collection.get("name"),
        "release_year": int(release_date[:4]) if release_date[:4].isdigit() else None,
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
    print(f"{len(tmdb_ids)} movies with a TMDB id, {len(missing)} to fetch")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for start in range(0, len(missing), BATCH_SIZE):
            batch = missing[start : start + BATCH_SIZE]
            cache.update(zip(batch, pool.map(lambda tmdb_id: fetch_details(tmdb_id, api_key), batch), strict=True))
            CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {min(start + BATCH_SIZE, len(missing))}/{len(missing)}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_movie_meta(movie: dict[str, str], details: dict[str, Any]) -> dict[str, Any]:
    """One movie in the backend's format (as v1 + v2), title without the year as in notebook 01."""
    year_match = TITLE_YEAR.search(movie["title"])
    year = int(year_match.group(1)) if year_match else details["release_year"]
    return {
        "id": int(movie["movieId"]),
        "title": TITLE_YEAR.sub("", movie["title"]),
        "year": year,
        "genres": [] if movie["genres"] == NO_GENRES else movie["genres"].split("|"),
        "poster": POSTER_BASE_URL + details["poster_path"] if details["poster_path"] else None,
        "overview": details["overview"],
        "original_language": details["original_language"],
        "collection_id": details["collection_id"],
        "collection_name": details["collection_name"],
    }


def main(env_path: Path) -> None:
    movie2idx: dict[str, int] = json.loads((PROCESSED_DIR / "movie2idx.json").read_text(encoding="utf-8"))
    rating_counts: list[int] = json.loads((PROCESSED_DIR / "movie_rating_counts_v3.json").read_text(encoding="utf-8"))
    links = read_csv_rows(RAW_DIR / "links.csv")
    tmdb_id_by_movie_id = {row["movieId"]: row["tmdbId"] for row in links if row["tmdbId"]}
    movies = [row for row in read_csv_rows(RAW_DIR / "movies.csv") if row["movieId"] in movie2idx]
    assert len(movies) == len(movie2idx), "movies.csv is missing movies that the model knows"

    cache: dict[str, Any] = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    tmdb_ids = [tmdb_id_by_movie_id[m["movieId"]] for m in movies if m["movieId"] in tmdb_id_by_movie_id]
    fill_cache(tmdb_ids, read_api_key(env_path), cache)

    movies_meta = [
        build_movie_meta(movie, cache.get(tmdb_id_by_movie_id.get(movie["movieId"], ""), NOT_ON_TMDB))
        for movie in movies
    ]
    with_poster = [m for m in movies_meta if m["poster"]]
    popular = sorted(with_poster, key=lambda m: rating_counts[movie2idx[str(m["id"])]], reverse=True)[:N_POPULAR]
    OUTPUT_PATH.write_text(
        json.dumps({"movies": movies_meta, "home_lists": {"popular": [m["id"] for m in popular]}}), encoding="utf-8"
    )

    print(f"saved {OUTPUT_PATH}: {len(movies_meta)} movies")
    print(f"  no poster: {len(movies_meta) - len(with_poster)}")
    print(f"  no year: {sum(m['year'] is None for m in movies_meta)}")
    print(f"  in a franchise: {sum(m['collection_id'] is not None for m in movies_meta)}")
    print(f"  Japanese: {sum(m['original_language'] == 'ja' for m in movies_meta)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
