"""Custom exceptions for the pylinky library."""

from typing import Any


class PyLinkyError(Exception):
    """Base exception for all pylinky errors."""


class InvalidTokenError(PyLinkyError):
    """Raised when the JWT token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class PRMAccessError(PyLinkyError):
    """Raised when the token doesn't grant access to the requested PRM."""

    def __init__(self, prm: str) -> None:
        self.prm = prm
        super().__init__(f"Token does not grant access to PRM {prm}")


class APIError(PyLinkyError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        status_code: int,
        message: str | None = None,
        response_body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        msg = f"API error {status_code}"
        if message:
            msg = f"{msg}: {message}"
        super().__init__(msg)


class AuthenticationError(APIError):
    """Raised when authentication fails (401 response)."""

    def __init__(self, message: str | None = None, response_body: Any = None) -> None:
        super().__init__(401, message or "Authentication failed", response_body)


class BadRequestError(APIError):
    """Raised when the request is malformed (400 response)."""

    def __init__(self, message: str | None = None, response_body: Any = None) -> None:
        super().__init__(400, message or "Bad request", response_body)


class ServerError(APIError):
    """Raised when the server returns an error (5xx response)."""

    def __init__(
        self, status_code: int = 500, message: str | None = None, response_body: Any = None
    ) -> None:
        super().__init__(status_code, message or "Server error", response_body)
