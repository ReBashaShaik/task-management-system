"""Log a short summary for every HTTP request without changing its response."""
import logging
from time import perf_counter

logger = logging.getLogger("task_management.requests")


class RequestLoggingMiddleware:
    """ASGI middleware that records method, path, status, and elapsed time."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = perf_counter()
        response_status = 500

        async def capture_response_status(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        await self.app(scope, receive, capture_response_status)
        elapsed_ms = (perf_counter() - started_at) * 1000
        path = scope.get("path", "")
        logger.info("%s %s -> %s (%.1f ms)", scope["method"], path,
                    response_status, elapsed_ms)
