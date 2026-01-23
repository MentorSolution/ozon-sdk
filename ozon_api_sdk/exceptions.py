from typing import Any


class OzonAPIError(Exception):
    """Base exception for Ozon API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class OzonAuthError(OzonAPIError):
    """Authentication or authorization error."""

    pass


class OzonRateLimitError(OzonAPIError):
    """Rate limit exceeded error."""

    pass
