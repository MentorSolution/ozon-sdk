import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Callable, Self

import httpx

from ozon_api_sdk.exceptions import OzonAPIError, OzonAuthError, OzonRateLimitError


@dataclass
class RetryConfig:
    """Configuration for retry behavior on transient errors.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 5).
        base_delay: Initial delay in seconds before first retry (default: 1.0).
        max_delay: Maximum delay between retries (default: 60.0).
        exponential_base: Multiplier for exponential backoff (default: 2.0).
        jitter: Add random jitter to delays to avoid thundering herd (default: True).
        retry_on_statuses: HTTP status codes to retry on (default: 429, 500, 502, 503, 504).
        on_retry: Optional callback called before each retry with (attempt, delay, error).
    """

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)
    on_retry: Callable[[int, float, Exception], None] | None = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay


@dataclass
class ReportPollingProgress:
    """Progress information during report polling.

    Attributes:
        report_uuid: UUID of the report being polled.
        attempt: Current polling attempt (1-based).
        max_attempts: Maximum polling attempts configured.
        status: Current report status from API.
        elapsed_seconds: Total seconds elapsed since polling started.
        next_poll_in: Seconds until next poll (None if this is final attempt).
    """

    report_uuid: str
    attempt: int
    max_attempts: int
    status: str | None
    elapsed_seconds: float
    next_poll_in: float | None = None

    @property
    def progress_percent(self) -> float:
        """Polling progress as percentage (0-100)."""
        return (self.attempt / self.max_attempts) * 100

    def __str__(self) -> str:
        status_str = self.status or "UNKNOWN"
        return (
            f"Report {self.report_uuid}: attempt {self.attempt}/{self.max_attempts} "
            f"({self.progress_percent:.0f}%) - status: {status_str}, "
            f"elapsed: {self.elapsed_seconds:.1f}s"
        )


class BaseAPIClient(ABC):
    """Base async API client with rate limiting, retry logic, and error handling."""

    def __init__(
        self,
        base_url: str,
        max_concurrent_requests: int = 10,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize base API client.

        Args:
            base_url: Base URL for API requests.
            max_concurrent_requests: Max parallel requests (default: 10).
            timeout: Request timeout in seconds (default: 30).
            retry_config: Retry configuration for transient errors (default: RetryConfig()).
        """
        self._base_url = base_url
        self._timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._client: httpx.AsyncClient | None = None
        self._retry_config = retry_config or RetryConfig()

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        await self._on_client_ready()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _on_client_ready(self) -> None:
        """Hook called after client initialization. Override for setup logic."""
        pass

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Return headers for API requests. Must be implemented by subclasses."""
        raise NotImplementedError

    def _parse_response(self, response: httpx.Response) -> tuple[dict[str, Any], Exception | None]:
        """Parse API response and return data with optional exception.

        Returns:
            Tuple of (response_data, exception_or_none).
            If exception is not None, it should be raised after retry logic.
        """
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code in (401, 403):
            return data, OzonAuthError(
                message=data.get("message", "Authentication failed"),
                status_code=response.status_code,
                response_data=data,
            )

        if response.status_code == 429:
            return data, OzonRateLimitError(
                message=data.get("message", "Rate limit exceeded"),
                status_code=response.status_code,
                response_data=data,
            )

        if response.status_code >= 400:
            return data, OzonAPIError(
                message=data.get("message", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_data=data,
            )

        return data, None

    def _should_retry(self, response: httpx.Response) -> bool:
        """Check if request should be retried based on status code."""
        return response.status_code in self._retry_config.retry_on_statuses

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with rate limiting and automatic retry on transient errors.

        Implements exponential backoff with jitter for 429 and 5xx errors.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        merged_headers = {**self._get_headers(), **(headers or {})}
        last_exception: Exception | None = None

        for attempt in range(self._retry_config.max_retries + 1):
            async with self._semaphore:
                try:
                    response = await self._client.request(
                        method=method.upper(),
                        url=endpoint,
                        json=json,
                        params=params,
                        headers=merged_headers,
                    )
                except httpx.RequestError as e:
                    # Network errors - retry
                    last_exception = OzonAPIError(
                        message=f"Request failed: {e}",
                        status_code=None,
                    )
                    if attempt < self._retry_config.max_retries:
                        delay = self._retry_config.calculate_delay(attempt)
                        if self._retry_config.on_retry:
                            self._retry_config.on_retry(attempt + 1, delay, last_exception)
                        await asyncio.sleep(delay)
                        continue
                    raise last_exception from e

                data, exception = self._parse_response(response)

                if exception is None:
                    return data

                # Don't retry auth errors
                if isinstance(exception, OzonAuthError):
                    raise exception

                # Check if we should retry
                if self._should_retry(response) and attempt < self._retry_config.max_retries:
                    delay = self._retry_config.calculate_delay(attempt)

                    # Use Retry-After header if present (common for 429)
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = max(float(retry_after), delay)
                        except ValueError:
                            pass

                    if self._retry_config.on_retry:
                        self._retry_config.on_retry(attempt + 1, delay, exception)

                    await asyncio.sleep(delay)
                    last_exception = exception
                    continue

                raise exception

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise OzonAPIError("Request failed after retries")

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make POST request."""
        return await self._request("POST", endpoint, json=data, **kwargs)

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make GET request."""
        return await self._request("GET", endpoint, params=params, **kwargs)
