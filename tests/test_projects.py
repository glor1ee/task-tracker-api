import pytest

pytestmark = pytest.mark.anyio


async def test_tasks_gets_nested_project(client, headers):
    project = (
        await client.post("/projects/", json={"name": "Test Project"}, headers=headers)
    ).json()

    task = (
        await client.post(
            "/tasks/", json={"title": "Test Task", "project_id": project["id"]}, headers=headers
        )
    ).json()

    assert task["project"]["name"] == "Test Project"


async def test_filter_tasks_by_project(client, headers):
    a = (await client.post("/projects/", json={"name": "Test Project A"}, headers=headers)).json()
    b = (await client.post("/projects/", json={"name": "Test Project B"}, headers=headers)).json()
    await client.post("/tasks/", json={"title": "a-1", "project_id": a["id"]}, headers=headers)
    await client.post("/tasks/", json={"title": "b-1", "project_id": b["id"]}, headers=headers)

    tasks = (await client.get(f"/tasks/?project_id={a['id']}", headers=headers)).json()
    for task in tasks:
        print(task)
    assert [t["project"]["id"] for t in tasks] == [a["id"]]


async def test_task_with_unknown_project(client, headers):
    response = await client.post(
        "/tasks/", json={"title": "Test Task", "project_id": 999}, headers=headers
    )

    assert response.status_code == 404


async def test_deleting_project_deletes_its_tasks(client, headers):
    project = (
        await client.post("/projects/", json={"name": "Test Project"}, headers=headers)
    ).json()
    await client.post(
        "/tasks/", json={"title": "Test Task", "project_id": project["id"]}, headers=headers
    )

    await client.delete(f"/projects/{project['id']}", headers=headers)

    assert (await client.get("/tasks/", headers=headers)).json() == []


async def test_duplicate_project_name_returns_409(client, headers):
    await client.post("/projects/", json={"name": "Test Project"}, headers=headers)

    response = await client.post("/projects/", json={"name": "Test Project"}, headers=headers)
    assert response.status_code == 409
