# API test cases: beginner walkthrough

Use this guide with Swagger at `http://127.0.0.1:8001/docs` or import the Postman collection at `postman/Task-Management-API.postman_collection.json`.

## Before testing

- Keep the API running. If you use Docker, the address is usually `http://localhost:8000`; this local walkthrough uses port `8001`.
- Use a new, valid `@gmail.com` address each time you test registration. Addresses such as `user@example.com` are rejected, and the API does not allow duplicate emails.
- Register one `project_manager` and one `member`. The manager creates the project and tasks; the member is assigned to a task.
- For protected requests, use the **Authorize** button in Swagger or send `Authorization: Bearer <access_token>` in Postman.
- In Swagger, `/auth/login` uses form fields named `email` and `password`. Enter the email used during registration.
- After login, copy `access_token`, click **Authorize**, and paste the token. Swagger adds the `Bearer` prefix for protected requests.
- An admin cannot register publicly. Set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` before starting the app to create one. The currently running local demo admin is `admin.local@gmail.com` with password `LocalAdminPass123!`.

## Sample users and values

Use your own unused emails if these accounts already exist:

```json
{
  "name": "Sam Manager",
  "email": "sam.manager@gmail.com",
  "password": "StrongPass123!",
  "role": "project_manager"
}
```

```json
{
  "name": "Lee Member",
  "email": "lee.member@gmail.com",
  "password": "StrongPass123!",
  "role": "member"
}
```

Remember the `id` returned for the member. You will use it as `assignee_id` when creating a task. Also remember the returned `project_id`, `task_id`, and `comment_id` for later requests.

## Endpoint test cases

### 1. Health check

**GET `/health`** — no token required.

Expected: `200 OK` and `{ "status": "ok" }`.

### 2. Register a member or project manager

**POST `/auth/register`** — no token required.

Use one of the sample JSON bodies above. Change the `role` to `member` when creating the team member.

Expected: `201 Created`; response contains the new user id, name, email, role, and active flag. The password is not returned.

Try registering with an email that already exists: expected `409 Conflict`. Try role `admin`: expected `422`; admin accounts are created through bootstrap settings instead.

Try `user1@example.com` for registration or login: expected `422 Unprocessable Entity` with a message that the email must end with `@gmail.com`.

### 3. Log in and get a token

**POST `/auth/login`** — no token required. Send form data, not JSON:

```text
email=sam.manager@gmail.com
password=StrongPass123!
```

Expected: `200 OK` with `access_token` and `token_type: bearer`. Repeat with the member's email to get the member token. In Swagger, click **Authorize** and paste the token to use protected endpoints.

Wrong password: expected `401 Unauthorized`.

### 4. Create a project

**POST `/projects`** — project manager or admin token.

```json
{
  "name": "Website Refresh",
  "description": "Update the public website"
}
```

Expected: `201 Created`. Save the returned `id` as `project_id`. A member token should receive `403 Forbidden`.

### 5. List projects with pagination

**GET `/projects?skip=0&limit=20`** — any signed-in user.

Expected: `200 OK` and a list of projects. Try `skip=0&limit=1` to see one result per page. `skip` cannot be negative; `limit` must be from 1 to 100.

### 6. Get project details and task summary

**GET `/projects/{project_id}`** — any signed-in user.

Example: `GET /projects/1`.

Expected: `200 OK`, project information, and `task_summary` with counts for `todo`, `in_progress`, `review`, and `done`.

### 7. Create and assign a task

**POST `/projects/{project_id}/tasks`** — owning project manager or admin token.

```json
{
  "assignee_id": 2,
  "title": "Build the landing page",
  "description": "Implement the approved design",
  "priority": "high",
  "due_date": "2026-11-10"
}
```

Replace `2` with the member id returned during registration. Expected: `201 Created`; save the returned `id` as `task_id`. Status starts as `todo`. Try assigning to a non-member or inactive user: expected `400 Bad Request`.

### 8. List and filter tasks in a project

**GET `/projects/{project_id}/tasks`** — signed-in user.

Try these query strings:

- No filters: `/projects/1/tasks`
- By status and priority: `/projects/1/tasks?status=todo&priority=high`
- By assignee: `/projects/1/tasks?assignee_id=2`

Expected: `200 OK` and a list. Members see only their assigned tasks, even when they request another `assignee_id`. Managers can access task lists only in their own projects. Try an invalid value such as `status=waiting`: expected `422`.

### 9. Get task details

**GET `/tasks/{task_id}`** — signed-in user with access to the task.

Expected: `200 OK` with the task. A member trying a task assigned to someone else gets `404`; a manager trying a task from another manager's project gets `403`.

### 10. View your assigned tasks

**GET `/my/tasks`** — signed-in user.

Expected: `200 OK` and tasks assigned to the current user. Log in as the member to see the sample task.

### 11. Move task status forward

**PATCH `/tasks/{task_id}/status`** — assigned member token only.

Send one next status at a time:

```json
{ "status": "in_progress" }
```

Then send `review`, and then `done`, using the same endpoint. Expected: `200 OK` after each valid step. The manager or another member should receive `403`. Trying to skip directly from `todo` to `review`, move backwards, or move beyond `done` returns `400`.

### 12. Update task details

**PUT `/tasks/{task_id}`** — owning project manager or admin token.

```json
{
  "title": "Build and review the landing page",
  "description": "Use the approved design and check it on mobile",
  "priority": "critical",
  "due_date": "2026-11-15"
}
```

Expected: `200 OK` with updated task details. A member or a manager who does not own the project should receive `403`.

### 13. Delete a task

**DELETE `/tasks/{task_id}`** — owning project manager or admin token.

Expected: `204 No Content`. Try as a member or a manager from another project: expected `403`. Delete this task only after you finish any comment tests for it.

### 14. Add a comment

**POST `/tasks/{task_id}/comments`** — any signed-in user.

```json
{ "content": "I have started this task and will share an update soon." }
```

Expected: `201 Created`. Save the returned `id` as `comment_id`.

### 15. List comments for a task

**GET `/tasks/{task_id}/comments`** — any signed-in user.

Expected: `200 OK` and comments with their author ids and creation times.

### 16. Delete a comment

**DELETE `/comments/{comment_id}`** — comment author or admin token.

Expected: `204 No Content`. Another member who did not write the comment should receive `403`.

### 17. Delete a project and check cascade deletion

**DELETE `/projects/{project_id}`** — admin token only. This is a destructive test; run it after finishing the other tests.

Expected: `204 No Content`. The project's tasks and their comments are deleted with it. A member or project manager should receive `403`.

## Full beginner test order

1. Health check.
2. Register manager and member; log in as each.
3. Create a project as manager; list projects and view project summary.
4. Create a task assigned to the member; list and filter tasks.
5. Log in as the member; view `/my/tasks`, open the task, move its status through each allowed step, and add a comment.
6. List and delete the comment as its author. Try another user's token once to confirm the permission check.
7. Log in as manager; update task details and delete a separate test task.
8. Log in as admin; delete the project last and confirm its remaining tasks/comments are gone.

Swagger shows each request and response shape. It also has a **Try it out** button so you can send requests without Postman.
