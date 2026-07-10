import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_byudzhetirovanie.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.db.session import Base, engine, SessionLocal
from app.infrastructure.db.seed import seed_database


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()


@pytest.fixture(scope="session")
def setup_db():
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/auth/login", json={"email": "analyst@example.com", "password": "valid_password"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    resp = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
