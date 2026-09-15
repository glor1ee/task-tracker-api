from datetime import timedelta

import pytest
from sqlalchemy import select

from app import models, security

pytestmark = pytest.mark.anyio


async def login(client, email="user@example.com", password="password1234"):
    await client.post("/auth/register", json={"email": email, "password": password})
    response = await client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


async def test_login_returns_refresh_token(client):
    tokens = await login(client)

    assert tokens["access_token"]
    assert tokens["refresh_token"]


async def test_refresh_rotates_token(client):
    old = (await login(client))["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": old})

    assert response.status_code == 200
    new = response.json()["refresh_token"]
    assert new != old
    assert (await client.post("/auth/refresh", json={"refresh_token": new})).status_code == 200


async def test_reused_refresh_token_revokes_whole_family(client):
    old = (await login(client))["refresh_token"]
    new = (await client.post("/auth/refresh", json={"refresh_token": old})).json()["refresh_token"]

    assert (await client.post("/auth/refresh", json={"refresh_token": old})).status_code == 401
    assert (await client.post("/auth/refresh", json={"refresh_token": new})).status_code == 401


async def test_logout_revokes_refresh_token(client):
    refresh = (await login(client))["refresh_token"]

    assert (await client.post("/auth/logout", json={"refresh_token": refresh})).status_code == 204
    assert (await client.post("/auth/refresh", json={"refresh_token": refresh})).status_code == 401


async def test_expired_refresh_token_rejected(client, db_session):
    refresh = (await login(client))["refresh_token"]
    token = (await db_session.scalars(select(models.RefreshToken))).one()
    token.expires_at = security.utcnow() - timedelta(seconds=1)
    await db_session.commit()

    assert (await client.post("/auth/refresh", json={"refresh_token": refresh})).status_code == 401


async def test_unknown_refresh_token_rejected(client):
    assert (await client.post("/auth/refresh", json={"refresh_token": "nope"})).status_code == 401


async def test_refresh_token_stored_as_hash(client, db_session):
    refresh = (await login(client))["refresh_token"]
    stored = (await db_session.scalars(select(models.RefreshToken))).one()

    assert stored.token_hash != refresh
    assert stored.token_hash == security.hash_token(refresh)
