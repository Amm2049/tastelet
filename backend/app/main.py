"""App factory: loads artifacts once at startup, sets CORS, turns errors into plain 422 messages."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import ALLOWED_ORIGINS, ARTIFACTS_DIR, MAX_PICKS, MIN_PICKS
from app.repositories.artifacts import load_artifacts
from app.services.recommender import UnknownMovieError, recommend_for_picks

PICK_COUNT_MESSAGE = f"Pick between {MIN_PICKS} and {MAX_PICKS} movies."


def plain_validation_message(error: RequestValidationError) -> str:
    """One sentence the frontend can show as is, instead of Pydantic's error list."""
    first = error.errors()[0]
    if first["type"] in {"too_short", "too_long"}:
        return PICK_COUNT_MESSAGE
    if first["type"] == "value_error":
        return str(first["msg"]).removeprefix("Value error, ").capitalize() + "."
    return 'Send JSON like {"movie_ids": [1, 2, 3, 4, 5]} with 5 to 10 movie ids.'


async def validation_error_handler(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    return JSONResponse(status_code=422, content={"detail": plain_validation_message(error)})


async def unknown_movie_handler(_: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": f"{error}."})


def create_app(artifacts_dir: Path = ARTIFACTS_DIR) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        artifacts = load_artifacts(artifacts_dir)  # once, not per request
        # PyTorch's first fold-in pays ~1 s of one-time setup; pay it here, not on the first user.
        recommend_for_picks(artifacts, artifacts.home_lists["popular"][:MIN_PICKS])
        app.state.artifacts = artifacts
        yield

    app = FastAPI(title="Tastelet API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"]
    )
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(UnknownMovieError, unknown_movie_handler)
    app.include_router(router)
    return app


app = create_app()
