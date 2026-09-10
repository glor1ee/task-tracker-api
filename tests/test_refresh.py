from datetime import timedelta

from sqlalchemy import select

from app import models, security


def login(client, email="user@example.com", password="password1234"):
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def test_login_returns_refresh_token(client):
    tokens = login(client)

    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_refresh_rotates_token(client):
    old = login(client)["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": old})

    assert response.status_code == 200
    new = response.json()["refresh_token"]
    assert new != old
    assert client.post("/auth/refresh", json={"refresh_token": new}).status_code == 200


def test_reused_refresh_token_revokes_whole_family(client):
    old = login(client)["refresh_token"]
    new = client.post("/auth/refresh", json={"refresh_token": old}).json()["refresh_token"]

    assert client.post("/auth/refresh", json={"refresh_token": old}).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": new}).status_code == 401


def test_logout_revokes_refresh_token(client):
    refresh = login(client)["refresh_token"]

    assert client.post("/auth/logout", json={"refresh_token": refresh}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_expired_refresh_token_rejected(client, db_session):
    refresh = login(client)["refresh_token"]
    token = db_session.scalars(select(models.RefreshToken)).one()
    token.expires_at = security.utcnow() - timedelta(seconds=1)
    db_session.commit()

    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_unknown_refresh_token_rejected(client):
    assert client.post("/auth/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_refresh_token_stored_as_hash(client, db_session):
    refresh = login(client)["refresh_token"]
    stored = db_session.scalars(select(models.RefreshToken)).one()

    assert stored.token_hash != refresh
    assert stored.token_hash == security.hash_token(refresh)