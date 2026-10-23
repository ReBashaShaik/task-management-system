"""Create the FastAPI application and connect its route groups."""
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from middleware.exception_handlers import register_exception_handlers
from middleware.request_logging import RequestLoggingMiddleware
from routers import auth, comments, projects, tasks
from utils.rate_limit import limiter

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="A simple API for projects, tasks, and team comments.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
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
