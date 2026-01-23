from typing import Any

from ozon_api_sdk.base import BaseAPIClient


class SellerAPIClient(BaseAPIClient):
    """Ozon Seller API client.

    Uses Client-Id and Api-Key headers for authentication.
    API documentation: https://docs.ozon.ru/api/seller/

    Usage:
        async with SellerAPIClient(client_id=123456, api_key="your-key") as client:
            response = await client.post("/v2/product/list", {"limit": 100})
    """

    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(
        self,
        client_id: int | str,
        api_key: str,
        *,
        max_concurrent_requests: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Seller API client.

        Args:
            client_id: Ozon Seller Client-Id.
            api_key: Ozon Seller Api-Key.
            max_concurrent_requests: Max parallel requests (default: 10).
            timeout: Request timeout in seconds (default: 30).
        """
        super().__init__(
            base_url=self.BASE_URL,
            max_concurrent_requests=max_concurrent_requests,
            timeout=timeout,
        )
        self._client_id = str(client_id)
        self._api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        return {
            "Client-Id": self._client_id,
            "Api-Key": self._api_key,
            "Content-Type": "application/json",
        }
