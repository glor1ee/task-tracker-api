import pytest

pytestmark = pytest.mark.anyio


async def test_register_and_login(client):
    response = await client.post(
        "/auth/register", json={"email": "account@example.com", "password": "password1234"}
    )

    assert response.status_code == 201
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()

    token = await client.post(
        "/auth/token", data={"username": "account@example.com", "password": "password1234"}
    )
    assert token.status_code == 200
    assert token.json()["token_type"] == "bearer"


async def test_login_with_wrong_password(client, auth_headers):
    await auth_headers("user@example.com")

    response = await client.post(
        "/auth/token", data={"username": "user@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


async def test_duplicate_email(client, auth_headers):
    await auth_headers("user@example.com")

    response = await client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 409


async def test_tasks_require_auth(client):
    assert (await client.get("/tasks/")).status_code == 401
    assert (await client.post("/tasks/", json={"title": "x"})).status_code == 401
    assert (await client.get("/projects/")).status_code == 401


async def test_invalid_token_rejected(client):
    assert (
        await client.get("/tasks/", headers={"Authorization": "Bearer broken"})
    ).status_code == 401


async def test_user_sees_only_own_tasks(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    await client.post("/tasks/", json={"title": "Test"}, headers=alice)

    assert (await client.get("/tasks/", headers=bob)).json() == []


async def test_user_cannot_touch_foreign_project(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    project = (
        await client.post("/projects/", json={"name": "Alice project"}, headers=alice)
    ).json()

    assert (await client.get("/projects/", headers=bob)).json() == []
    assert (await client.get(f"/projects/{project['id']}", headers=bob)).status_code == 404
    assert (await client.delete(f"/projects/{project['id']}", headers=bob)).status_code == 404


async def test_same_project_name_for_different_users(client, auth_headers):
    alice = await auth_headers("alice@example.com")
    bob = await auth_headers("bob@example.com")
    await client.post("/projects/", json={"name": "Project 1"}, headers=alice)

    response = await client.post("/projects/", json={"name": "Project 1"}, headers=bob)

    assert response.status_code == 201
