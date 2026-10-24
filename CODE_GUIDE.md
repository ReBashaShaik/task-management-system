# Task Management System - Code Guide

This guide explains how the current project works, file by file and function by function, in simple English. For install and run commands, see README.md. For example requests, see API_TEST_CASES.md.

## 1. Request flow
```text
HTTP request -> FastAPI router -> Pydantic schema -> service -> SQLAlchemy session -> database
```
Routers handle HTTP input. Schemas validate values. Services apply business rules. Models describe database tables. This separation keeps each part focused.

## 2. Roles and business rules
- A project manager creates projects and tasks, and assigns tasks to active members.
- Members view their assigned tasks, update status, and add comments.
- Admins can manage tasks across projects, delete projects, and delete comments.
- Status moves only one step at a time: `todo` -> `in_progress` -> `review` -> `done`.
- Priorities are `low`, `medium`, `high`, and `critical`.
- Registration and login need valid `@gmail.com` emails and passwords of 8 to 72 characters.
- Public registration allows only `member` and `project_manager`. Admins are created from bootstrap settings.
- Only the assignee can change a task status. A manager can manage tasks only in projects they own; admins can manage any project.
- A task assignee must be an active account with the `member` role.
- Any signed-in user can add or list comments on an existing task. Only the author or an admin can delete a comment.
- Signed-in users can list and read project details. Project task access has role checks.
- Project lists are paginated; task and comment lists are not.
- `is_active` is checked during login and protected requests. There is no user activate/deactivate endpoint.

## 3. Database tables (`models.py`)
- `User`: ID, name, unique email, password hash, role, and active flag. One user can manage projects, receive tasks, and write comments.
- `Project`: manager foreign key, name, optional description, creation time. One project has many tasks.
- `Task`: project and assignee foreign keys, title, optional description, status, priority, optional due date, creation time. One task has many comments.
- `Comment`: task and author foreign keys, text, and creation time.
- Foreign keys connect records. Project deletion cascades to tasks, and task deletion cascades to comments. User references use `RESTRICT`; there is no user-delete endpoint.
- SQLAlchemy relationships such as `project.tasks` let Python navigate the connections; they are not API routes.

## 4. Startup, settings, database
### `main.py`
- `FastAPI(...)` creates the app and sets the title/version used in Swagger.
- `app.state.limiter` attaches the shared SlowAPI limiter; its exception handler returns rate-limit errors.
- `app.add_middleware(...)` enables request logging.
- `register_exception_handlers(app)` registers the common service-error handler.
- `app.include_router(...)` adds authentication, project, task, and comment routes.
- `health_check()` handles `GET /health` and returns `{"status":"ok"}`. Docker uses it for its health check.

### `config.py`
- `Settings` defines database URL, JWT secret, token lifetime, and optional bootstrap admin email/password.
- `model_config` reads `.env` and ignores extra settings.
- `settings = Settings()` loads settings once. Environment variables can override `.env`.

### `database.py`
- `Base` is the parent for SQLAlchemy models and holds their metadata.
- `engine` creates connections from the configured database URL. SQLite gets special connection settings.
- `SessionLocal` creates database sessions.
- `enable_sqlite_foreign_keys()` enables SQLite foreign keys so tests follow MySQL cascade behavior.

### `dependencies.py`
- `get_db()` opens a database session for a request and always closes it.
- `get_current_user()` reads the Bearer token, checks its signature and expiry, loads the user, and rejects missing/invalid/expired tokens or inactive users with 401.
- `require_manager_or_admin()` allows only a manager or admin; other roles get 403.
- `bearer_scheme` describes Bearer authentication to FastAPI and Swagger.

## 5. Validation (`schemas.py`)
- `Role`, `Status`, `Priority` define allowed values.
- `require_gmail_address(email)` requires the `gmail.com` domain. `EmailStr` checks email format; `GmailEmail` combines both rules.
- `UserCreate` validates registration. `name_must_not_be_blank()` trims the name and rejects spaces-only values. Admin is not a permitted public role.
- `UserOut` returns safe user fields and excludes the password hash. `from_attributes` allows reading SQLAlchemy objects.
- `ProjectCreate` validates project name and optional description. `ProjectOut` defines project response fields. `ProjectDetail` adds counts by task status.
- `TaskCreate` validates assignee, title, description, priority, and due date. Priority defaults to medium; model default status is todo.
- `TaskUpdate` permits assignee, title, description, priority, and due date changes. `check_update_fields()` rejects an empty body and null for assignee/title/priority; omitted fields stay unchanged.
- `TaskStatusUpdate` validates one status. `TaskOut` defines task response fields.
- `CommentCreate` requires 1-5000 characters. `CommentOut` defines comment response fields.
- Pydantic input failures normally return HTTP 422.

## 6. Passwords and tokens (`utils/security.py`)
- `password_context` configures bcrypt.
- `hash_password(password)` creates a one-way hash before storage.
- `verify_password(password, hashed_password)` checks a submitted password against its hash.
- `create_access_token(user_id)` signs a JWT with the user ID and expiry time.
- `read_token_user_id(token)` validates signature/expiry and returns the user ID, or `None` for a bad token.
- Clients send a token as `Authorization: Bearer <token>`. The token is not the password.

## 7. Authentication
### `routers/auth.py`
- `register(request, data, db)` handles `POST /auth/register`: JSON input, schema validation, rate limiting, service call, safe user response, HTTP 201.
- `login(request, email, password, db)` handles `POST /auth/login`: form fields (not JSON), email/password checks, rate limiting, service call, JWT response.
### `services/auth_service.py`
- `register_user(data, db)` rejects duplicate email, hashes the password, creates/saves a user, and returns it.
- `login_user(email, password, db)` finds the account, verifies password and active status, and returns an access token. Login failures share one error message.
- Both auth endpoints have a limit of 30 requests per minute per client IP. The limiter uses in-memory storage for one API instance.

## 8. Project routes and functions
### `routers/projects.py`
| Function | Route | Purpose |
|---|---|---|
| `create_project()` | `POST /projects` | Manager/admin only; validates and creates a project (201). |
| `list_projects()` | `GET /projects?skip=0&limit=20` | Signed-in user; validates skip and limit (maximum 100). |
| `get_project()` | `GET /projects/{project_id}` | Signed-in user; returns project and status counts. |
| `delete_project()` | `DELETE /projects/{project_id}` | Admin only in service; success is 204 with no body. |
### `services/project_service.py`
- `create_project(data, manager, db)` saves the signed-in user as the manager.
- `list_projects(skip, limit, db)` orders by ID and returns one page. It does not filter by manager.
- `get_project(project_id, db)` returns project and count for each status; absent statuses count as zero; missing project raises 404.
- `delete_project(project_id, user, db)` checks admin role, finds and deletes project, commits; cascades remove tasks/comments.

## 9. Task routes and functions
### `routers/tasks.py`
| Function | Route | Purpose |
|---|---|---|
| `create_task()` | `POST /projects/{project_id}/tasks` | Manager/admin route; service checks project and assignee; returns 201. |
| `list_project_tasks()` | `GET /projects/{project_id}/tasks` | Signed-in user; optional status, priority, and assignee_id filters. |
| `my_tasks()` | `GET /my/tasks` | Returns current user assigned tasks. |
| `get_task()` | `GET /tasks/{task_id}` | Service checks viewing permission. |
| `update_task_status()` | `PATCH /tasks/{task_id}/status` | Service checks assignee and status order. |
| `update_task()` | `PUT /tasks/{task_id}` | Manager/admin route; service checks project ownership. |
| `delete_task()` | `DELETE /tasks/{task_id}` | Manager/admin route; success is 204. |
### `services/task_service.py`
- `STATUS_FLOW` sets status order; `PRIORITIES` lists priority names.
- `get_task_or_raise(task_id, db)` finds task or raises 404.
- `check_project_manager(user, project)` allows admin anywhere, manager only in own project.
- `check_assignee(assignee_id, db)` requires an existing, active member.
- `create_task(project_id, data, user, db)` checks project, manager ownership, and assignee; creates/saves task.
- `list_project_tasks(...)` checks project exists; blocks managers from others projects; limits members to their own tasks; applies optional filters; sorts by ID.
- `list_my_tasks(user, db)` returns tasks assigned to the signed-in user, ordered by ID.
- `get_task(task_id, user, db)` allows admin; checks manager owns the project; checks member is assignee. Another member task is returned as 404.
- `update_task_status(task_id, new_status, user, db)` allows only assignee, requires exactly next status, blocks changing a completed task, then saves.
- `update_task(task_id, data, user, db)` checks ownership/admin access, checks a new assignee if supplied, changes only supplied fields, and saves.
- `delete_task(task_id, user, db)` checks manager/admin access, deletes and commits; comments cascade.

## 10. Comment routes and functions
### `routers/comments.py`
| Function | Route | Purpose |
|---|---|---|
| `add_comment()` | `POST /tasks/{task_id}/comments` | Signed-in user; validates text; returns 201. |
| `list_comments()` | `GET /tasks/{task_id}/comments` | Signed-in user; returns comments ordered by ID. |
| `delete_comment()` | `DELETE /comments/{comment_id}` | Service permits author/admin; success is 204. |
### `services/comment_service.py`
- `add_comment(task_id, data, user, db)` checks task exists, uses signed-in user as author, saves and returns comment.
- `list_comments(task_id, db)` checks task exists and returns comments ordered by ID.
- `delete_comment(comment_id, user, db)` checks comment exists, permits author/admin, deletes and commits.

## 11. Errors, logs, rate limits
### `services/errors.py`
- `ServiceError` stores readable message and status.
- `AuthenticationError` is 401; `NotFoundError` 404; `ForbiddenError` 403; `ConflictError` 409; `InvalidRequestError` 400.
### `middleware/exception_handlers.py`
- `register_exception_handlers(app)` registers service-error handling.
- `handle_service_error()` returns `{"detail":"message"}` and the matching status. Authentication errors include `WWW-Authenticate: Bearer`.
- FastAPI handles schema errors as 422; SlowAPI returns 429.
### `middleware/request_logging.py`
- `RequestLoggingMiddleware.__init__(app)` stores the downstream application.
- `RequestLoggingMiddleware.__call__(scope, receive, send)` passes non-HTTP traffic through; for HTTP it times the request, captures status, and logs method/path/status/duration without changing the response.
### `utils/rate_limit.py`
- `limiter` uses client IP as the rate-limit key. Register and login each allow 30 requests/minute. The in-memory limit is for one API instance.

## 12. Admin bootstrap (`bootstrap.py`)
- `create_bootstrap_admin(reset_password=False)` skips without both admin settings. It leaves an existing admin unchanged by default or creates a missing admin with a hashed password.
- With reset enabled it verifies the configured email belongs to an admin, then replaces the hash. It will not promote a non-admin.
- The command-line parser accepts `--reset-password`. Docker runs bootstrap at startup; use `docker compose exec api python -m bootstrap --reset-password` to deliberately reset the password from `.env`.

## 13. Alembic migrations
### `alembic/env.py`
- Imports models so Alembic sees all tables and reads the database URL from settings.
- `run_migrations_offline()` configures a migration without a live connection.
- `run_migrations_online()` opens a database connection and runs migration steps.
- The final condition selects offline or online mode.
### `alembic/versions/0001_initial_tables.py`
- `upgrade()` creates users, projects, tasks, comments, columns, keys, indexes, enums, and defaults.
- `downgrade()` drops the tables in dependency-safe order.
- Docker runs `alembic upgrade head` before the API. Future schema changes should use new revision files.

## 14. Tests
### `tests/conftest.py`
- `test_engine` creates an in-memory SQLite database; `enable_test_foreign_keys()` enables SQLite foreign keys.
- `TestSession` makes sessions for test setup and checks.
- `client()` creates tables, overrides `get_db`, provides FastAPI TestClient, then clears the override and drops the tables.
- `register(...)` creates a test user; `login(...)` returns a Bearer authorization header.
### `tests/test_task_rules.py`
- `setup_task()` creates manager, member, project, task, and login credentials.
- `test_only_assignee_can_move_task_to_next_status` checks who can change status.
- `test_task_status_must_follow_the_defined_order` rejects skipped steps.
- `test_only_comment_author_or_admin_can_delete_comment` checks comment delete rights.
- `test_public_registration_cannot_create_admin` rejects public admin registration.
- `test_registration_and_login_validate_and_use_email` checks email, Gmail, password, and login form.
- `test_project_delete_message_is_clear_for_manager_and_member` checks project delete permission/message.
- `test_protected_endpoint_without_token_returns_clear_401` checks missing login.
- `test_member_can_only_read_and_filter_their_assigned_tasks` checks member scoping and filter.
- `test_manager_cannot_read_or_manage_another_managers_tasks` checks manager ownership and project visibility.
- `test_admin_project_delete_cascades_to_tasks_and_comments` checks cascade delete.
- `test_all_required_endpoints_have_a_successful_happy_path` exercises the complete endpoint flow.
- `test_task_update_rejects_empty_or_null_required_fields` checks task update validation.
- `test_login_is_rate_limited` checks that the 31st login gets 429.
Run tests with `python -m pytest -q tests`; setup commands are in README.md.

## 15. Docker and settings files
### `Dockerfile`
Uses Python 3.11 slim, installs requirements, copies code, defines a `/health` check, then runs Alembic, admin bootstrap, and Uvicorn on port 8000.
### `docker-compose.yml`
- `db` runs MySQL 8; named volume `mysql_data` keeps data after containers stop.
- Host MySQL port is `127.0.0.1:3307`; API uses service name `db` and internal port 3306.
- API binds to local `127.0.0.1:8000`, waits for database health, and has a health check.
- `docker compose down` keeps data; `docker compose down -v` deletes the database volume and its records.
### `.env.example`, `.env`, `requirements.txt`
Copy `.env.example` to private `.env`, then replace placeholder secrets. Never commit `.env`. Requirements pin FastAPI, Uvicorn, SQLAlchemy, Alembic, PyMySQL, JWT, bcrypt, form parsing, settings, email validation, pytest, HTTPX, SlowAPI, and aiofiles. There is no upload route; aiofiles is currently unused.

## 16. API route list
| Method and path | Purpose |
|---|---|
| `POST /auth/register` | Register member or manager. |
| `POST /auth/login` | Login with email/password form and receive JWT. |
| `POST /projects` | Create project. |
| `GET /projects` | Paginated projects. |
| `GET /projects/{project_id}` | Project and task counts. |
| `DELETE /projects/{project_id}` | Admin deletes project and related data. |
| `POST /projects/{project_id}/tasks` | Create and assign task. |
| `GET /projects/{project_id}/tasks` | List tasks and optional filters. |
| `GET /tasks/{task_id}` | Read task if permitted. |
| `PATCH /tasks/{task_id}/status` | Assignee advances task status. |
| `PUT /tasks/{task_id}` | Manager/admin edits task. |
| `DELETE /tasks/{task_id}` | Manager/admin deletes task. |
| `POST /tasks/{task_id}/comments` | Signed-in user adds comment. |
| `GET /tasks/{task_id}/comments` | Signed-in user lists comments. |
| `DELETE /comments/{comment_id}` | Author/admin removes comment. |
| `GET /my/tasks` | Current user's tasks. |
| `GET /health` | Health response. |
Common response codes: 200 success; 201 created; 204 deleted; 400 invalid business action; 401 not logged in; 403 no permission; 404 missing/inaccessible record; 409 duplicate email; 422 invalid input; 429 rate limit.

## 17. Not included
- No endpoint changes user role, active state, or deletes users. `is_active` defaults true and is checked during authentication; a database operator must change it directly.
- The API is publicly deployed on Render at https://task-management-system-api-lkwx.onrender.com/docs and uses Aiven MySQL. This repository provides a backend API; it does not include a graphical frontend.
- No file upload route exists even though aiofiles is installed.
- Task and comment lists are not paginated.

This guide explains current behavior. Update it when the code changes.