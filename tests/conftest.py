"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """HTTP client with lifespan (creates upload root via patched ``UPLOADS_ROOT``)."""
    with TestClient(app) as test_client:
        yield test_client
