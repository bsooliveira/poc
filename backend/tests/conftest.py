import os

os.environ.update(
    ENVIRONMENT="development",
    AUTH_MODE="local",
    LLM_PROVIDER="demo",
    EMBEDDING_PROVIDER="hash",
)

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import initialize
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.cache_clear()
    initialize()
    with TestClient(app) as client:
        client.headers["X-SimplFAQ"] = "local-poc"
        yield client
    settings.cache_clear()
