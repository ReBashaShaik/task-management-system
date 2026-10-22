# Role-based API testing checklist

Use this checklist in Swagger UI. Tick each box as you test it. The API uses a local SQLite database when `.env` is absent, and this checklist assumes the server is running at `http://127.0.0.1:8001`.

Open **http://127.0.0.1:8001/docs**. For protected endpoints, click **Authorize** and paste the access token for the role named in that step. The login endpoint uses form fields named `email` and `password`. If Swagger is authorized as another role, click **Logout** in the authorization window first.

## Sample accounts

Use unused email addresses. If one is already registered, change the email and use that new email to log in.

| Account | Registration role | Email | Password |
|---|---|---|---|
| Manager | `project_manager` | `check.manager@gmail.com` | `StrongPass123!` |
| Member 1 | `member` | `check.member1@gmail.com` | `StrongPass123!` |
| Member 2 (permission checks) | `member` | `check.member2@gmail.com` | `StrongPass123!` |
| Admin | bootstrap only | Use the admin email/password you configured before starting the app | Use your configured password |

Admin accounts cannot be created using `/auth/register`. For a local SQLite run, set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in PowerShell and run `python -m bootstrap` before logging in. The README has the full startup steps.

## 1. Health and account setup

- [ ] **GET `/health`** — no authorization. Click **Try it out**, then **Execute**. Expect `200` and `{"status":"ok"}`.
- [ ] **POST `/auth/register` — manager** — no authorization. Send:

  ```json
  {
    "name": "Check Manager",
    "email": "check.manager@gmail.com",
    "password": "StrongPass123!",
    "role": "project_manager"
  }
  ```

  Expect `201`. Save the returned `id` if you want it for reference.
- [ ] **POST `/auth/register` — member 1** — same shape, with `name` = `Check Member One`, email = `check.member1@gmail.com`, and `role` = `member`. Expect `201`. Save the returned `id` as **MEMBER1_ID**.
- [ ] **POST `/auth/register` — member 2** — same shape, with `name` = `Check Member Two`, email = `check.member2@gmail.com`, and `role` = `member`. Expect `201`. Save its id as **MEMBER2_ID**.
- [ ] **POST `/auth/login` — manager, member 1, and member 2** — login with each account using the `email` field and its password. Expect `200` and an `access_token` for each account.
- [ ] **Admin login** — use the configured bootstrap admin email and password at **POST `/auth/login`**. Expect `200`. Save the admin token if testing in Postman; Swagger’s **Authorize** can log in with these credentials.
- [ ] **Negative check: public admin registration** — try **POST `/auth/register`** with `"role": "admin"`. Expect `422`; public registration must not grant admin access.

## 2. Projects — authorize as manager

- [ ] **POST `/projects`** — manager token. Send:

  ```json
  {
    "name": "Checklist Project",
    "description": "Project created while testing the API"
  }
  ```

  Expect `201`. Save the returned `id` as **PROJECT_ID**.
- [ ] **GET `/projects?skip=0&limit=20`** — manager token. Expect `200` and find “Checklist Project”. Try `skip=0&limit=1` to check pagination.
- [ ] **GET `/projects/{project_id}`** — use **PROJECT_ID**, manager token. Expect `200` and a `task_summary` with counts for `todo`, `in_progress`, `review`, and `done`.
- [ ] **Negative check: create project as member** — authorize as member 1 and call **POST `/projects`** with the same body. Expect `403`.

## 3. Tasks — authorize as manager to create them

- [ ] **POST `/projects/{project_id}/tasks` — task for member 1** — manager token. Replace the path value with **PROJECT_ID** and use **MEMBER1_ID** below:

  ```json
  {
    "assignee_id": 1,
    "title": "Task for member one",
    "description": "Use this task to test the status flow and comments",
    "priority": "high",
    "due_date": "2026-11-10"
  }
  ```

  Replace `1` with the actual **MEMBER1_ID**. Expect `201`; save the returned task `id` as **TASK1_ID**. Its initial status should be `todo`.
- [ ] **POST `/projects/{project_id}/tasks` — disposable task for deletion** — manager token, same path. Assign it to member 1 and use:

  ```json
  {
    "assignee_id": 1,
    "title": "Disposable task",
    "description": "This task is only for testing delete",
    "priority": "low"
  }
  ```

  Replace `1` with **MEMBER1_ID**. Expect `201`; save its id as **DELETE_TASK_ID**.
- [ ] **POST `/projects/{project_id}/tasks` — task for member 2** — manager token, same path. Assign it to **MEMBER2_ID**, title it `Task for member two`, priority `medium`. Expect `201`; save its id as **TASK2_ID**.
- [ ] **GET `/projects/{project_id}/tasks`** — manager token. Expect `200` and all three tasks.
- [ ] **GET `/projects/{project_id}/tasks?status=todo&priority=high`** — manager token. Expect `200`; the response should include TASK1_ID.
- [ ] **GET `/projects/{project_id}/tasks?assignee_id={MEMBER1_ID}`** — manager token. Expect only tasks assigned to member 1.
- [ ] **GET `/tasks/{task_id}` — manager view** — use **TASK1_ID** and manager token. Expect `200` because this manager owns the project.
- [ ] **GET `/my/tasks` — member 1 view** — authorize as member 1. Expect `200` and only tasks assigned to member 1.
- [ ] **GET `/tasks/{task_id}` — member 1 own task** — use **TASK1_ID** and member 1 token. Expect `200`.
- [ ] **Negative check: member 1 reads member 2 task** — use **TASK2_ID** and member 1 token at **GET `/tasks/{task_id}`**. Expect `404`.
- [ ] **Negative check: member 1 filters for member 2** — call **GET `/projects/{project_id}/tasks?assignee_id={MEMBER2_ID}** with member 1 token. Expect an empty list; members cannot use the filter to see another person's tasks.
- [ ] **Negative check: manager updates another manager's task** — this requires a second project owned by a second manager. If you create one, trying **PUT** or **DELETE `/tasks/{task_id}`** on that project's task with the first manager token should return `403`.

## 4. Status updates — authorize as the assigned member

Use **TASK1_ID**. Send one request at a time and check the returned `status` after each one.

- [ ] **PATCH `/tasks/{task_id}/status`** with `{"status":"in_progress"}` as member 1. Expect `200`; status becomes `in_progress`.
- [ ] Repeat with `{"status":"review"}` as member 1. Expect `200`; status becomes `review`.
- [ ] Repeat with `{"status":"done"}` as member 1. Expect `200`; status becomes `done`.
- [ ] **Negative check: manager tries to change status** — try this on **DELETE_TASK_ID** with manager authorization and body `{"status":"in_progress"}`. Expect `403`.
- [ ] **Negative check: skip a status step** — create another task for member 1, then try changing it directly from `todo` to `review`. Expect `400`.
- [ ] **Negative check: invalid status value** — send `{"status":"waiting"}`. Expect `422`.

## 5. Task details — authorize as manager

- [ ] **PUT `/tasks/{task_id}`** — use **TASK1_ID** and manager token. Send:

  ```json
  {
    "title": "Updated checklist task",
    "description": "The manager changed the task details",
    "priority": "critical",
    "due_date": "2026-11-15"
  }
  ```

  Expect `200` and the changed fields in the response. At least one field must be sent.
- [ ] **Negative check: member updates task details** — call the same endpoint and body using member 1 authorization. Expect `403`.
- [ ] **Negative check: empty update** — send `{}` as manager. Expect `422`.
- [ ] **Negative check: invalid priority** — send `{"priority":"urgent"}` as manager. Expect `422`.

## 6. Comments

- [ ] **POST `/tasks/{task_id}/comments`** — use **TASK1_ID**, authorize as member 1, and send:

  ```json
  { "content": "I started this task and will share progress here." }
  ```

  Expect `201`; save the comment `id` as **COMMENT_ID**.
- [ ] **GET `/tasks/{task_id}/comments`** — use **TASK1_ID** and any signed-in user. Expect `200` and find the comment.
- [ ] **Negative check: another member deletes the comment** — use member 2 authorization with **DELETE `/comments/{comment_id}`** and **COMMENT_ID**. Expect `403`.
- [ ] **DELETE `/comments/{comment_id}` — author deletes own comment** — use member 1 authorization and **COMMENT_ID**. Expect `204`.
- [ ] **Admin comment check (optional)** — add a new comment, then delete it using admin authorization. Expect `204`.

### Admin full-access checks (optional)

These checks use a separate temporary project so they do not affect the manager's main test project.

- [ ] As admin, **POST `/projects`** with `{"name":"Admin Access Check","description":"Temporary admin test"}`. Expect `201`; save its id as **ADMIN_PROJECT_ID**.
- [ ] As admin, **POST `/projects/{project_id}/tasks`** under **ADMIN_PROJECT_ID**, assigning it to **MEMBER1_ID**, with title `Admin-created task` and priority `medium`. Expect `201`; save its id as **ADMIN_TASK_ID**.
- [ ] As admin, call **GET `/projects/{project_id}/tasks`**, **GET `/tasks/{task_id}`**, and **PUT `/tasks/{task_id}`** using **ADMIN_PROJECT_ID** and **ADMIN_TASK_ID**. Expect `200` for each. For the update, send `{"title":"Admin-updated task"}`.
- [ ] As admin, call **DELETE `/tasks/{task_id}`** using **ADMIN_TASK_ID**, then **DELETE `/projects/{project_id}`** using **ADMIN_PROJECT_ID**. Expect `204` for both.

## 7. Delete task and project last

- [ ] **DELETE `/tasks/{task_id}`** — use **DELETE_TASK_ID** and manager authorization. Expect `204`. This removes only the disposable task.
- [ ] **Admin can delete a task (optional)** — if you create another disposable task, admin authorization should also return `204` for its delete request.
- [ ] **Negative check: member deletes task** — try deleting a remaining task as a member. Expect `403`.
- [ ] **DELETE `/projects/{project_id}` — admin only** — authorize as the bootstrap admin and use **PROJECT_ID**. Do this last; expect `204`.
- [ ] **Cascade check** — after project deletion, use **GET `/projects/{project_id}`**. Expect `404`. Its tasks and comments should also have been removed with it.
- [ ] **Negative check: manager deletes project** — before doing the admin delete, try as manager. Expect `403`.

## Endpoint coverage

This checklist covers: `GET /health`; registration and login; all project routes; all project task routes; task details, status, update, and delete; comment create, list, and delete; and `GET /my/tasks`.

When you finish, tell me which boxes passed and copy the **status code** and **response body** for any failed request. Do not send access tokens or passwords.
