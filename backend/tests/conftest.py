import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def analyst_headers(client):
    token = _token(client, "analyst@example.com", "valid_password")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    token = _token(client, "admin@example.com", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def object_a(client, analyst_headers):
    response = client.get("/api/construction-objects", headers=analyst_headers)
    assert response.status_code == 200
    return response.json()[0]


@pytest.fixture()
def demo_scenario(client, analyst_headers):
    response = client.get("/api/scenarios", headers=analyst_headers)
    assert response.status_code == 200
    scenarios = response.json()
    assert scenarios
    return scenarios[0]
