# Task Management System API

A beginner-friendly REST API for managing projects, tasks, and team comments. Project managers create projects and assign work. Members update task progress and discuss the work with comments.

## Contents

- [What this project includes](#what-this-project-includes)
- [Roles and permissions](#roles-and-permissions)
- [Technology](#technology)
- [Project layout](#project-layout)
- [Run the project with Docker](#run-the-project-with-docker)
- [Sign in and try the API](#6-sign-in-and-try-the-api)
- [API endpoint list](#api-endpoint-list)
- [Run the tests](#run-the-tests)
- [Useful Docker commands](#useful-docker-commands)
- [Troubleshooting](#troubleshooting)
- [More project guides](#more-project-guides)
- [Free public deployment guide](DEPLOYMENT_FREE.md)
- [Deployment status](#deployment-status)

## What this project includes

- User registration and JWT login.
- Projects, tasks, and comments stored in MySQL 8.
- Role-based access for members, project managers, and admins.
- Task status and priority validation, plus task filtering.
- Alembic database migrations.
- Docker Compose setup for the API and MySQL.
- Automated tests with pytest and HTTPX.
- A health endpoint at `/health`.

Registration accepts valid `@gmail.com` email addresses. New users can register as `member` or `project_manager`. Admin accounts are created from private environment settings when the application starts; public registration cannot create an admin.

## Roles and permissions

| Role | Main permissions |
| --- | --- |
| `member` | View assigned tasks, move the status of their own assigned task, add comments, and delete their own comments. |
| `project_manager` | Create projects and tasks, assign tasks, and manage tasks in projects they own. |
| `admin` | Full access, including deleting projects, managing tasks, and deleting comments. |

Task status values are `todo`, `in_progress`, `review`, and `done`. Priority values are `low`, `medium`, `high`, and `critical`. A task status can only be changed by its assignee, and it must move through the next step in the status flow.

## Technology

- Python 3.11
- FastAPI and Pydantic v2
- SQLAlchemy and Alembic
- MySQL 8
- JWT authentication with `python-jose` and password hashing with bcrypt
- Docker and Docker Compose
- pytest and HTTPX
- SlowAPI rate limits on registration and login

## Project layout

```text
task-management-system/
|-- alembic/              Database migration setup and migration files
|-- middleware/           Request logging and shared error handling
|-- routers/              HTTP endpoints grouped by resource
|-- services/             Application and business rules
|-- tests/                Automated tests
|-- utils/                Shared helpers such as rate limiting
|-- main.py               FastAPI application entry point
|-- models.py             SQLAlchemy database tables and relationships
|-- schemas.py            Request and response validation
|-- database.py           Database connection setup
|-- dependencies.py       Authentication and shared request dependencies
|-- bootstrap.py          Creates or resets the configured admin account
|-- Dockerfile            Instructions for building the API image
|-- docker-compose.yml    API and MySQL local environment
|-- requirements.txt      Python packages
`-- .env.example          Safe example environment settings
```

## Run the project with Docker

Docker is the recommended way to run the API and MySQL together. You do not need to install MySQL separately. These instructions are for a fresh checkout.

### 1. Install the prerequisites

Install Git and Docker Desktop for Windows, Mac, or Linux. Start Docker Desktop and wait until it says Docker is running. Check Docker in a new terminal:

```shell
docker --version
docker compose version
```

### 2. Download the project

Open PowerShell on Windows, or Terminal on Mac/Linux, and run:

```shell
git clone https://github.com/ReBashaShaik/task-management-system.git
cd task-management-system
```

If the project is already on your computer, open a terminal in the project folder instead.

### 3. Create your private `.env` file

Copy the example settings file.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Mac/Linux:

```shell
cp .env.example .env
```

Open `.env` in a text editor. Replace the example values with your own private passwords and a long random secret. For an easy first run, use letters and numbers in the MySQL passwords. The database password is part of the Docker Compose connection URL, so special URL characters may need encoding.

Example shape only. Do not use these sample passwords for a real account:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
BOOTSTRAP_ADMIN_EMAIL=admin@gmail.com
BOOTSTRAP_ADMIN_PASSWORD=choose-a-strong-private-password
MYSQL_DATABASE=task_management
MYSQL_USER=task_user
MYSQL_PASSWORD=choose-a-database-password
MYSQL_ROOT_PASSWORD=choose-a-different-root-password
```

Keep `.env` private. Do not commit it or send it to anyone. `.env.example` contains placeholders and is safe to share. The admin email and password in `.env` are for the admin account created by the bootstrap step; public registration only allows member and project-manager accounts.

### 4. Build and start the API and database

From the project folder, run:

```shell
docker compose up -d --build
```

On the first run, Docker downloads the MySQL image and builds the API image. The API waits for MySQL, applies Alembic migrations, creates the configured admin account if needed, and then starts the web server. The first run can take a few minutes.

### 5. Check that the services are running

```shell
docker compose ps
```

Wait until the database is healthy and the API is running. Open these addresses in a browser:

- Swagger API page: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

The health check should return:

```json
{"status":"ok"}
```

### 6. Sign in and try the API

1. Open Swagger at `http://localhost:8000/docs`.
2. Use `POST /auth/register` to create a member or project manager. Enter a valid Gmail address and a password with 8 to 72 characters.
3. Use `POST /auth/login`. Swagger asks for form fields named `email` and `password`; enter the same credentials used during registration.
4. Copy the `access_token` from the response.
5. Click **Authorize** near the top of Swagger and paste the token. Swagger adds it to protected requests.
6. As a project manager, create a project with `POST /projects`.
7. Create a task with `POST /projects/{project_id}/tasks`. Set `assignee_id` to the ID of a registered member.
8. Sign in as that member to view assigned tasks with `GET /my/tasks`, update task status, and add comments.

The local API listens on `http://localhost:8000`. The MySQL container is available from this computer on port `3307`; inside Docker, the API connects to the database using the Compose service name.

## API endpoint list

Protected endpoints require a valid JWT. In Swagger, use **Authorize** after login.

| Method | Endpoint | Purpose | Access summary |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Register a member or project manager. | Public; Gmail address required. |
| `POST` | `/auth/login` | Get a JWT access token. | Public; email and password form fields. |
| `POST` | `/projects` | Create a project. | Project manager or admin. |
| `GET` | `/projects?skip=0&limit=20` | List projects with pagination. | Signed-in user. |
| `GET` | `/projects/{project_id}` | Get project details and task counts by status. | Signed-in user. |
| `DELETE` | `/projects/{project_id}` | Delete a project and its related data. | Admin. |
| `POST` | `/projects/{project_id}/tasks` | Create and assign a task. | Project manager for their project, or admin. |
| `GET` | `/projects/{project_id}/tasks` | List tasks; supports `status`, `priority`, and `assignee_id` filters. | Signed-in user with access. |
| `GET` | `/tasks/{task_id}` | Get task details. | Signed-in user with access. |
| `PATCH` | `/tasks/{task_id}/status` | Move an assigned task to the next status. | The task assignee. |
| `PUT` | `/tasks/{task_id}` | Update task details. | Project manager for their project, or admin. |
| `DELETE` | `/tasks/{task_id}` | Delete a task. | Project manager for their project, or admin. |
| `POST` | `/tasks/{task_id}/comments` | Add a comment. | Signed-in user with access to the task. |
| `GET` | `/tasks/{task_id}/comments` | List task comments. | Signed-in user with access to the task. |
| `DELETE` | `/comments/{comment_id}` | Delete a comment. | Comment author or admin. |
| `GET` | `/my/tasks` | List tasks assigned to the signed-in user. | Signed-in user. |
| `GET` | `/health` | Check whether the API is responding. | Public. |

Registration and login are limited to 30 requests per minute per client IP address.

## Run the tests

The tests use a temporary SQLite database, so you do not need to start MySQL to run them. Run these commands from the project folder.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q tests
```

If PowerShell blocks virtual-environment activation, allow scripts for this terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Mac/Linux

```shell
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests
```

## Useful Docker commands

| What you want to do | Command |
| --- | --- |
| See running services | `docker compose ps` |
| Follow API logs | `docker compose logs -f api` |
| Follow database logs | `docker compose logs -f db` |
| Stop services and keep database data | `docker compose down` |
| Start services again | `docker compose up -d` |
| Rebuild and start the API | `docker compose up -d --build api` |
| Reset the configured admin password from `.env` | `docker compose exec api python -m bootstrap --reset-password` |
| Open a MySQL prompt | `docker compose exec db mysql -u root -p` |

When MySQL asks for a password, enter the `MYSQL_ROOT_PASSWORD` value from your private `.env` file. To view registered users after connecting, run:

```sql
USE task_management;
SELECT id, name, email, role, is_active FROM users ORDER BY id DESC;
```

`docker compose down` keeps database records in the Docker volume. `docker compose down -v` deletes that volume and all database records. Use the `-v` version only when you intentionally want to erase the local database.

## Troubleshooting

### Docker command is not found

Open or restart Docker Desktop, then close and reopen PowerShell. Run `docker --version` again. If it is still not found, restart the computer after installing Docker Desktop.

### Port 8000 is already in use

Another API process may already be listening on port 8000. Stop the other process (for example, stop a local Uvicorn server with `Ctrl+C`) and retry `docker compose up -d`.

### API is still starting or Swagger cannot open

Wait a little, then check `docker compose ps` and `docker compose logs -f api`. The API starts after MySQL is healthy and migrations finish.

### Login returns an invalid email or password error

Use the exact Gmail address and password used during registration. For the bootstrap admin, use `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` from `.env`. If the admin password changed in the database, run the admin reset command in the Docker command table, then try again.

### MySQL data is not visible in the host MySQL client

The Docker database is separate from a MySQL server installed directly on your computer. This project maps the Docker database to `127.0.0.1:3307`, so connect to port `3307` to inspect it from a desktop MySQL client. Or use `docker compose exec db mysql -u root -p` as shown above.

## More project guides

- [API test cases](API_TEST_CASES.md) �w^~)�t sample data and a guided API testing sequence.
- [Role-based API checklist](ROLE_BASED_API_CHECKLIST.md)+�u���T checks to perform for each role.
- [Code guide](CODE_GUIDE.md)"��y��y� explanations of the main code areas.
- [Postman collection](postman/Task-Management-API.postman_collection.json)+�u���T import this file into Postman to try the API.
- [Project presentation](presentation/Task-Management-API-Guide.pptx) �w^~)�t architecture and API overview.

## Deployment status

The API is publicly deployed on Render and uses Aiven MySQL:

- Swagger UI: [https://task-management-system-api-lkwx.onrender.com/docs](https://task-management-system-api-lkwx.onrender.com/docs)
- Health check: [https://task-management-system-api-lkwx.onrender.com/health](https://task-management-system-api-lkwx.onrender.com/health)

The deployed registration flow has been checked. New public registrations are stored in the hosted Aiven database, not in the local Docker database. The Render free web service can spin down after 15 minutes without requests; the first request afterward may take about a minute to start. Free services are suitable for demos and learning, not production availability. See [DEPLOYMENT_FREE.md](DEPLOYMENT_FREE.md) for the setup and limitations. The Compose ports are bound to the local computer, so Compose remains for local development and demonstration.

## Security notes

- Use private, unique passwords and a long random `SECRET_KEY` in your own `.env` file.
- Do not commit `.env`, real passwords, JWT tokens, or other secrets to GitHub.
- The example credentials in `.env.example` are placeholders; replace them before starting the project.
- Passwords are stored as hashes, not as plain text.
