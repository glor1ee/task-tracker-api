import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, enable_sqlite_foreign_keys, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
is_sqlite = TEST_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {}
)

if is_sqlite:
    enable_sqlite_foreign_keys(engine)

TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    def _make(email: str = "user@example.com", password: str = "password1234") -> dict[str, str]:
        client.post("/auth/register", json={"email": email, "password": password})
        response = client.post("/auth/token", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make

@pytest.fixture
def headers(auth_headers):
    return auth_headers()