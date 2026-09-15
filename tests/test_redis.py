import pytest

pytestmark = pytest.mark.anyio


async def login(client, email="user@example.com", password="password1234"):
    await client.post("/auth/register", json={"email": email, "password": password})
    response = await client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


async def test_logout_revokes_access_token_immediately(client):
    tokens = await login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert (await client.get("/tasks/", headers=headers)).status_code == 200

    response = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )

    assert response.status_code == 204
    assert (await client.get("/tasks/", headers=headers)).status_code == 401


async def test_revoked_jti_lives_no_longer_than_the_token(client, redis):
    tokens = await login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )

    keys = [key async for key in redis.scan_iter("revoked_jti:*")]
    assert len(keys) == 1
    assert 0 < await redis.ttl(keys[0]) <= 30 * 60


async def test_logout_requires_access_token(client):
    tokens = await login(client)

    response = await client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


async def test_login_is_rate_limited(client):
    await client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password1234"}
    )
    for _ in range(5):
        response = await client.post(
            "/auth/token", data={"username": "user@example.com", "password": "wrong"}
        )
        assert response.status_code == 401

    response = await client.post(
        "/auth/token", data={"username": "user@example.com", "password": "password1234"}
    )

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
