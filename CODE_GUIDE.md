# Code guide for beginners

This guide explains the main files and what each function does in plain English.

## Application startup

- `main.py` creates the FastAPI app, adds middleware, connects each group of routes, and provides `/health`.
- `config.py` reads values such as the database address and JWT secret from environment variables or `.env`.
- `database.py` creates the database connection engine and `SessionLocal`, which makes a short-lived database session for each request.
- `dependencies.py` contains shared request helpers. `get_db` opens and closes the database session. `get_current_user` reads the bearer token and finds the active user. `require_manager_or_admin` blocks users without the required role.

## Data and validation

- `models.py` describes the four database tables and their relationships.
- `schemas.py` describes the JSON fields the API accepts and returns. Pydantic rejects invalid values before the business code uses them.
- `utils/security.py` hashes passwords before storage, checks a password during login, creates signed JWT tokens, and reads the user id from a token.

## Route functions

- `routers/`: each route reads HTTP input, gets the current user/database session, then calls one service function.
- `services/auth_service.py`: registers accounts and checks login details.
- `services/project_service.py`: creates, lists, summarizes, and deletes projects.
- `services/task_service.py`: applies project ownership, assignee, status-flow, filtering, update, and delete rules.
- `services/comment_service.py`: adds, lists, and deletes comments.
- `services/errors.py` and `middleware/exception_handlers.py`: turn expected business errors into clear HTTP responses.
- `middleware/request_logging.py`: logs request method, path, response status, and elapsed time.
- `bootstrap.py`: creates the first admin from environment settings once. Public registration intentionally does not allow the admin role.

## Request example in plain English

When someone changes task status, FastAPI first checks the JSON shape and loads the signed-in user. The router passes the request to `task_service.update_task_status`, which checks the assignee and status order, saves the change, and returns the updated task. This keeps HTTP handling separate from business rules.

## Database update flow

`alembic/versions/0001_initial_tables.py` creates the first version of the four tables. A future schema change should be recorded as a new Alembic revision, so a database can move forward or back in a controlled way.
