import os

import fakeredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base, enable_sqlite_foreign_keys, get_db
from app.main import app
from app.redis_client import get_redis

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
if TEST_DATABASE_URL.startswith("sqlite"):
    enable_sqlite_foreign_keys(engine)

TestSession = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def redis():
    # A separate in-memory server per test: counters and blacklists never leak between tests.
    client = fakeredis.FakeAsyncRedis(server=fakeredis.FakeServer(), decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
async def client(db_session, redis):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    async def _make(
        email: str = "user@example.com", password: str = "password1234"
    ) -> dict[str, str]:
        await client.post("/auth/register", json={"email": email, "password": password})
        response = await client.post("/auth/token", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make


@pytest.fixture
async def headers(auth_headers):
    return await auth_headers()
