def test_register_and_login(client):
    response = client.post("/auth/register", json={"email": "account@example.com",
                                                   "password": "password1234"})

    assert response.status_code == 201
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()

    token = client.post("/auth/token", data={"username": "account@example.com",
                                             "password": "password1234"})
    assert token.status_code == 200
    assert token.json()["token_type"] == "bearer"


def test_login_with_wrong_password(client, auth_headers):
    auth_headers("user@example.com")

    response = client.post("/auth/token", data={"username": "user@example.com",
                                                   "password": "wrong"})

    assert response.status_code == 401

def test_duplicate_email(client, auth_headers):
    auth_headers("user@example.com")

    response = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 409


def test_tasks_require_auth(client):
    assert client.get("/tasks/").status_code == 401
    assert client.post("/tasks/", json={"title": "x"}).status_code == 401
    assert client.get("/projects/").status_code == 401


def test_invalid_token_rejected(client):
    assert client.get("/tasks/", headers={"Authorization": "Bearer broken"}).status_code == 401


def test_user_sees_only_own_tasks(client, auth_headers):
    alice = auth_headers("alice@example.com")
    bob = auth_headers("bob@example.com")
    client.post("/tasks/", json={"title": "Test"}, headers=alice)

    assert client.get("/tasks/", headers=bob).json() == []


def test_user_cannot_touch_foreign_project(client, auth_headers):
    alice = auth_headers("alice@example.com")
    bob = auth_headers("bob@example.com")
    project = client.post("/projects/", json={"name": "Alice project"}, headers=alice).json()

    assert client.get("/projects/", headers=bob).json() == []
    assert client.get(f"/projects/{project['id']}", headers=bob).status_code == 404
    assert client.delete(f"/projects/{project['id']}", headers=bob).status_code == 404


def test_same_project_name_for_different_users(client, auth_headers):
    alice = auth_headers("alice@example.com")
    bob = auth_headers("bob@example.com")
    client.post("/projects/", json={"name": "Project 1"}, headers=alice)

    response = client.post("/projects/", json={"name": "Project 1"}, headers=bob)

    assert response.status_code == 201