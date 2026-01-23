from __future__ import annotations

from typing import TYPE_CHECKING

from ozon_api_sdk.base import BaseAPIClient, RetryConfig

if TYPE_CHECKING:
    from ozon_api_sdk.seller.products import ProductsAPI
    from ozon_api_sdk.seller.finance import FinanceAPI


class SellerAPIClient(BaseAPIClient):
    """Ozon Seller API client.

    Uses Client-Id and Api-Key headers for authentication.
    API documentation: https://docs.ozon.ru/api/seller/

    Features:
        - Retry with exponential backoff on 429/5xx errors
        - Rate limiting via semaphore

    Usage:
        async with SellerAPIClient(client_id=123456, api_key="your-key") as client:
            # Via subclients
            products = await client.products.get_products()
            transactions = await client.finance.get_transactions(date_from, date_to)

            # Direct API call
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
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize Seller API client.

        Args:
            client_id: Ozon Seller Client-Id.
            api_key: Ozon Seller Api-Key.
            max_concurrent_requests: Max parallel requests (default: 10).
            timeout: Request timeout in seconds (default: 30).
            retry_config: Retry configuration for 429/5xx errors.
                         Default: 5 retries with exponential backoff.
        """
        super().__init__(
            base_url=self.BASE_URL,
            max_concurrent_requests=max_concurrent_requests,
            timeout=timeout,
            retry_config=retry_config,
        )
        self._client_id = str(client_id)
        self._api_key = api_key

        # Lazy-initialized subclients
        self._products: ProductsAPI | None = None
        self._finance: FinanceAPI | None = None

    def _get_headers(self) -> dict[str, str]:
        return {
            "Client-Id": self._client_id,
            "Api-Key": self._api_key,
            "Content-Type": "application/json",
        }

    @property
    def products(self) -> ProductsAPI:
        """Products API subclient."""
        if self._products is None:
            from ozon_api_sdk.seller.products import ProductsAPI

            self._products = ProductsAPI(self)
        return self._products

    @property
    def finance(self) -> FinanceAPI:
        """Finance API subclient."""
        if self._finance is None:
            from ozon_api_sdk.seller.finance import FinanceAPI

            self._finance = FinanceAPI(self)
        return self._finance
