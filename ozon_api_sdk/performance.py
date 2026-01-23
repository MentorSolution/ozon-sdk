import time
from typing import Any

import httpx

from ozon_api_sdk.base import BaseAPIClient
from ozon_api_sdk.exceptions import OzonAuthError


class PerformanceAPIClient(BaseAPIClient):
    """Ozon Performance API client with automatic OAuth token management.

    Uses client_id/client_secret to obtain Bearer token.
    Token is automatically refreshed when expired.
    API documentation: https://docs.ozon.ru/api/performance/

    Usage:
        async with PerformanceAPIClient(
            client_id="your-client-id",
            client_secret="your-client-secret"
        ) as client:
            response = await client.get("/api/client/campaign")
    """

    BASE_URL = "https://api-performance.ozon.ru"
    TOKEN_ENDPOINT = "/api/client/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        max_concurrent_requests: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Performance API client.

        Args:
            client_id: Ozon Performance API client ID.
            client_secret: Ozon Performance API client secret.
            max_concurrent_requests: Max parallel requests (default: 10).
            timeout: Request timeout in seconds (default: 30).
        """
        super().__init__(
            base_url=self.BASE_URL,
            max_concurrent_requests=max_concurrent_requests,
            timeout=timeout,
        )
        self._perf_client_id = client_id
        self._perf_client_secret = client_secret
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def _on_client_ready(self) -> None:
        """Fetch access token when client is initialized."""
        await self._refresh_token()

    async def _refresh_token(self) -> None:
        """Fetch new access token from Performance API."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        try:
            response = await self._client.post(
                self.TOKEN_ENDPOINT,
                json={
                    "client_id": self._perf_client_id,
                    "client_secret": self._perf_client_secret,
                    "grant_type": "client_credentials",
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 1800)  # Default 30 min
            # Refresh 60 seconds before expiry
            self._token_expires_at = time.time() + expires_in - 60

        except httpx.HTTPStatusError as e:
            raise OzonAuthError(
                message=f"Failed to obtain access token: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise OzonAuthError(
                message=f"Token request failed: {e}",
            ) from e

    async def _ensure_token_valid(self) -> None:
        """Refresh token if expired or about to expire."""
        if time.time() >= self._token_expires_at:
            await self._refresh_token()

    def _get_headers(self) -> dict[str, str]:
        if not self._access_token:
            raise RuntimeError(
                "Access token not available. Use 'async with' context manager."
            )
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make request with automatic token refresh."""
        await self._ensure_token_valid()
        return await super()._request(method, endpoint, **kwargs)
