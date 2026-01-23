import asyncio
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Self

import httpx

from ozon_api_sdk.exceptions import OzonAPIError, OzonAuthError, OzonRateLimitError


class BaseAPIClient(ABC):
    """Base async API client with rate limiting and error handling."""

    def __init__(
        self,
        base_url: str,
        max_concurrent_requests: int = 10,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._client: httpx.AsyncClient | None = None

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

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code in (401, 403):
            raise OzonAuthError(
                message=data.get("message", "Authentication failed"),
                status_code=response.status_code,
                response_data=data,
            )

        if response.status_code == 429:
            raise OzonRateLimitError(
                message=data.get("message", "Rate limit exceeded"),
                status_code=response.status_code,
                response_data=data,
            )

        if response.status_code >= 400:
            raise OzonAPIError(
                message=data.get("message", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_data=data,
            )

        return data

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with rate limiting."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        merged_headers = {**self._get_headers(), **(headers or {})}

        async with self._semaphore:
            response = await self._client.request(
                method=method.upper(),
                url=endpoint,
                json=json,
                params=params,
                headers=merged_headers,
            )
            return self._handle_response(response)

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
