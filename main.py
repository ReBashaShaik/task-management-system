"""Create the FastAPI application and connect its route groups."""
from fastapi import FastAPI

from middleware.exception_handlers import register_exception_handlers
from middleware.request_logging import RequestLoggingMiddleware
from routers import auth, comments, projects, tasks

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="A simple API for projects, tasks, and team comments.",
)

app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Return a small response to show that the API is running."""
    return {"status": "ok"}
