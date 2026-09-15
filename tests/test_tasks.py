import pytest

pytestmark = pytest.mark.anyio


async def test_create_task(client, headers):
    response = await client.post("/tasks/", json={"title": "Test Task"}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test Task"
    assert body["is_done"] is False
    assert body["id"] > 0


async def test_create_task_with_empty_title(client, headers):
    response = await client.post("/tasks/", json={"title": ""}, headers=headers)

    assert response.status_code == 422


async def test_retrieve_missing_task(client, headers):
    response = await client.get("/tasks/50", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


async def test_patch_updates_only_sent_fields(client, headers):
    task = (
        await client.post(
            "/tasks/",
            json={"title": "Test title", "description": "test description"},
            headers=headers,
        )
    ).json()

    response = await client.patch(f"/tasks/{task['id']}", json={"is_done": True}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["is_done"] is True
    assert body["title"] == "Test title"
    assert body["description"] == "test description"


async def test_delete_task(client, headers):
    task = (await client.post("/tasks/", json={"title": "Test Task"}, headers=headers)).json()

    assert (await client.delete(f"/tasks/{task['id']}", headers=headers)).status_code == 204
    assert (await client.get(f"/tasks/{task['id']}", headers=headers)).status_code == 404


async def test_limit_is_validated(client, headers):
    assert (await client.get("/tasks/?limit=0", headers=headers)).status_code == 422
    assert (await client.get("/tasks/?limit=500", headers=headers)).status_code == 422
    assert (await client.get("/tasks/?skip=-1", headers=headers)).status_code == 422
