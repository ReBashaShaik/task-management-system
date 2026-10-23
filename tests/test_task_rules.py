from tests.conftest import TestSession, login, register
from models import Comment, Task, User
from utils.security import hash_password


def setup_task(client):
    register(client, "Manager", "manager@gmail.com", "project_manager")
    manager_headers = login(client, "manager@gmail.com")
    member = register(client, "Member", "member@gmail.com")
    project = client.post("/projects", json={"name": "Launch"}, headers=manager_headers).json()
    task = client.post(f"/projects/{project['id']}/tasks", json={
        "assignee_id": member["id"], "title": "Write welcome page", "priority": "high"
    }, headers=manager_headers).json()
    member_headers = login(client, "member@gmail.com")
    return manager_headers, member_headers, task


def test_only_assignee_can_move_task_to_next_status(client):
    manager_headers, member_headers, task = setup_task(client)
    manager_change = client.patch(f"/tasks/{task['id']}/status", json={"status": "in_progress"}, headers=manager_headers)
    assert manager_change.status_code == 403

    member_change = client.patch(f"/tasks/{task['id']}/status", json={"status": "in_progress"}, headers=member_headers)
    assert member_change.status_code == 200
    assert member_change.json()["status"] == "in_progress"


def test_task_status_must_follow_the_defined_order(client):
    _, member_headers, task = setup_task(client)
    response = client.patch(f"/tasks/{task['id']}/status", json={"status": "review"}, headers=member_headers)
    assert response.status_code == 400


def test_only_comment_author_or_admin_can_delete_comment(client):
    _, member_headers, task = setup_task(client)
    comment = client.post(f"/tasks/{task['id']}/comments", json={"content": "Started work"}, headers=member_headers).json()
    register(client, "Other member", "other@gmail.com")
    other_headers = login(client, "other@gmail.com")
    denied = client.delete(f"/comments/{comment['id']}", headers=other_headers)
    assert denied.status_code == 403
    allowed = client.delete(f"/comments/{comment['id']}", headers=member_headers)
    assert allowed.status_code == 204


def test_public_registration_cannot_create_admin(client):
    response = client.post("/auth/register", json={"name": "Bad Actor", "email": "bad@gmail.com",
        "password": "StrongPass123!", "role": "admin"})
    assert response.status_code == 422


def test_registration_and_login_validate_and_use_email(client):
    invalid_email = client.post("/auth/register", json={
        "name": "Invalid Email", "email": "not-an-email",
        "password": "StrongPass123!", "role": "member",
    })
    non_gmail_email = client.post("/auth/register", json={
        "name": "Non Gmail Email", "email": "user1@example.com",
        "password": "StrongPass123!", "role": "member",
    })
    short_password = client.post("/auth/register", json={
        "name": "Short Password", "email": "short@gmail.com",
        "password": "short", "role": "member",
    })
    assert invalid_email.status_code == 422
    assert non_gmail_email.status_code == 422
    assert "Email must end with @gmail.com" in str(non_gmail_email.json())
    assert short_password.status_code == 422

    register(client, "Email Login Member", "email.login@gmail.com")
    login_response = client.post("/auth/login", data={
        "email": "email.login@gmail.com", "password": "StrongPass123!",
    })
    invalid_login_email = client.post("/auth/login", data={
        "email": "not-an-email", "password": "StrongPass123!",
    })
    non_gmail_login = client.post("/auth/login", data={
        "email": "user1@example.com", "password": "StrongPass123!",
    })

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert invalid_login_email.status_code == 422
    assert non_gmail_login.status_code == 422
    assert "Email must end with @gmail.com" in str(non_gmail_login.json())


def test_project_delete_message_is_clear_for_manager_and_member(client):
    manager_headers, member_headers, task = setup_task(client)
    project_path = f"/projects/{task['project_id']}"

    manager_response = client.delete(project_path, headers=manager_headers)
    member_response = client.delete(project_path, headers=member_headers)

    for response in (manager_response, member_response):
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "You cannot delete this project. Only an admin can delete projects."
        )


def test_protected_endpoint_without_token_returns_clear_401(client):
    response = client.get("/projects")
    assert response.status_code == 401
    assert response.json()["detail"] == "Please log in and provide your bearer token."


def test_member_can_only_read_and_filter_their_assigned_tasks(client):
    manager_headers, member_headers, own_task = setup_task(client)
    other_member = register(client, "Another member", "another@gmail.com")
    project_id = own_task["project_id"]
    other_task = client.post(f"/projects/{project_id}/tasks", json={
        "assignee_id": other_member["id"], "title": "Private assigned task", "priority": "high"
    }, headers=manager_headers).json()

    project_tasks = client.get(f"/projects/{project_id}/tasks", headers=member_headers)
    filtered_tasks = client.get(
        f"/projects/{project_id}/tasks?assignee_id={other_member['id']}",
        headers=member_headers,
    )
    other_task_detail = client.get(f"/tasks/{other_task['id']}", headers=member_headers)

    assert [task["id"] for task in project_tasks.json()] == [own_task["id"]]
    assert filtered_tasks.json() == []
    assert other_task_detail.status_code == 404


def test_manager_cannot_read_or_manage_another_managers_tasks(client):
    _, _, task = setup_task(client)
    register(client, "Other manager", "other.manager@gmail.com", "project_manager")
    other_manager_headers = login(client, "other.manager@gmail.com")

    projects = client.get("/projects?skip=0&limit=20", headers=other_manager_headers)
    project_detail = client.get(f"/projects/{task['project_id']}", headers=other_manager_headers)
    assert any(project["id"] == task["project_id"] for project in projects.json())
    assert project_detail.status_code == 200
    assert client.get(f"/tasks/{task['id']}", headers=other_manager_headers).status_code == 403
    assert client.put(
        f"/tasks/{task['id']}",
        json={"title": "Not allowed"},
        headers=other_manager_headers,
    ).status_code == 403
    assert client.delete(f"/tasks/{task['id']}", headers=other_manager_headers).status_code == 403


def test_admin_project_delete_cascades_to_tasks_and_comments(client):
    _, member_headers, task = setup_task(client)
    comment = client.post(
        f"/tasks/{task['id']}/comments",
        json={"content": "This comment should be deleted with its project"},
        headers=member_headers,
    ).json()

    db = TestSession()
    db.add(User(name="Admin", email="admin@gmail.com",
                hashed_password=hash_password("StrongPass123!"), role="admin"))
    db.commit()
    db.close()
    admin_headers = login(client, "admin@gmail.com")

    deleted = client.delete(f"/projects/{task['project_id']}", headers=admin_headers)

    check_db = TestSession()
    task_still_exists = check_db.get(Task, task["id"]) is not None
    comment_still_exists = check_db.get(Comment, comment["id"]) is not None
    check_db.close()

    assert deleted.status_code == 204
    assert not task_still_exists
    assert not comment_still_exists


def test_all_required_endpoints_have_a_successful_happy_path(client):
    """Exercise every listed route from registration through project cleanup."""
    assert client.get("/health").json() == {"status": "ok"}

    manager = register(client, "Full Flow Manager", "full.manager@gmail.com", "project_manager")
    member = register(client, "Full Flow Member", "full.member@gmail.com")
    db = TestSession()
    db.add(User(name="Full Flow Admin", email="full.admin@gmail.com",
                hashed_password=hash_password("StrongPass123!"), role="admin"))
    db.commit()
    db.close()

    manager_headers = login(client, manager["email"])
    member_headers = login(client, member["email"])
    admin_headers = login(client, "full.admin@gmail.com")

    project_response = client.post("/projects", json={"name": "Full Flow Project"}, headers=manager_headers)
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]
    assert client.get("/projects?skip=0&limit=20", headers=member_headers).status_code == 200
    assert client.get(f"/projects/{project_id}", headers=member_headers).status_code == 200

    task_response = client.post(f"/projects/{project_id}/tasks", json={
        "assignee_id": member["id"], "title": "Full flow task", "priority": "high"
    }, headers=manager_headers)
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    assert client.get(f"/projects/{project_id}/tasks?status=todo&priority=high", headers=manager_headers).status_code == 200
    assert client.get(f"/tasks/{task_id}", headers=member_headers).status_code == 200
    assert client.get("/my/tasks", headers=member_headers).status_code == 200

    for next_status in ("in_progress", "review", "done"):
        response = client.patch(f"/tasks/{task_id}/status", json={"status": next_status}, headers=member_headers)
        assert response.status_code == 200

    assert client.put(f"/tasks/{task_id}", json={"title": "Updated full flow task"}, headers=manager_headers).status_code == 200
    comment_response = client.post(f"/tasks/{task_id}/comments", json={"content": "Progress update"}, headers=member_headers)
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["id"]
    assert client.get(f"/tasks/{task_id}/comments", headers=member_headers).status_code == 200
    assert client.delete(f"/comments/{comment_id}", headers=member_headers).status_code == 204

    cleanup_task = client.post(f"/projects/{project_id}/tasks", json={
        "assignee_id": member["id"], "title": "Task to delete"
    }, headers=manager_headers).json()
    assert client.delete(f"/tasks/{cleanup_task['id']}", headers=manager_headers).status_code == 204
    assert client.delete(f"/projects/{project_id}", headers=admin_headers).status_code == 204


def test_task_update_rejects_empty_or_null_required_fields(client):
    manager_headers, _, task = setup_task(client)

    empty_update = client.put(f"/tasks/{task['id']}", json={}, headers=manager_headers)
    null_title = client.put(f"/tasks/{task['id']}", json={"title": None}, headers=manager_headers)

    assert empty_update.status_code == 422
    assert null_title.status_code == 422

def test_login_is_rate_limited(client):
    """Repeated login attempts from one IP receive a clear 429 response."""
    from utils.rate_limit import limiter

    limiter.reset()
    login_data = {"email": "missing.user@gmail.com", "password": "StrongPass123!"}

    for _ in range(30):
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401

    limited_response = client.post("/auth/login", data=login_data)
    limiter.reset()

    assert limited_response.status_code == 429
