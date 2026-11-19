import pytest

from app.core.config import ARTIFACTS_DIR
from app.repositories.artifacts import Artifacts, load_artifacts


@pytest.fixture(scope="session")
def artifacts() -> Artifacts:
    return load_artifacts(ARTIFACTS_DIR)
