"""Simple errors raised by services and converted to HTTP responses centrally."""


class ServiceError(Exception):
    """Base error for a problem the API can explain to its caller."""

    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(ServiceError):
    status_code = 401


class NotFoundError(ServiceError):
    status_code = 404


class ForbiddenError(ServiceError):
    status_code = 403


class ConflictError(ServiceError):
    status_code = 409


class InvalidRequestError(ServiceError):
    status_code = 400
