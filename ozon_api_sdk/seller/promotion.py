from typing import TYPE_CHECKING, Any

from ozon_api_sdk.endpoints import SellerEndpoints
from ozon_api_sdk.exceptions import OzonPromotionError
from ozon_api_sdk.types import ActivateProduct, APIItemsList, APIResult

if TYPE_CHECKING:
    from ozon_api_sdk.seller.client import SellerAPIClient


class PromotionAPI:
    """Promotion API subclient for Seller API."""

    def __init__(self, client: "SellerAPIClient") -> None:
        self._client = client

    def _check_error(self, response: dict[str, Any]) -> None:
        """Check response for Promotion API errors.

        Raises:
            OzonPromotionError: If response contains an error.
        """
        code = response.get("code")
        if code is not None and not (200 <= code < 300):
            raise OzonPromotionError(
                message=response.get("message", "Unknown promotion error"),
                code=code,
                details=response.get("details", []),
            )
        if "message" in response and "result" not in response:
            raise OzonPromotionError(
                message=response["message"],
                code=code,
                details=response.get("details", []),
            )

    async def get_actions(self) -> APIItemsList:
        """Fetch list of available Ozon promotions.

        Returns:
            List of promotion dictionaries.

        Raises:
            OzonPromotionError: If API returns an error.
        """
        response = await self._client.get(SellerEndpoints.ACTIONS_LIST)
        self._check_error(response)
        return response.get("result", [])

    async def get_candidates(
        self,
        action_id: int,
        limit: int = 100,
        last_id: str = "",
        fetch_all: bool = False,
    ) -> APIItemsList | APIResult:
        """Fetch products that can participate in a promotion.

        Args:
            action_id: Promotion ID from get_actions().
            limit: Results per page (default: 100).
            last_id: Last item ID for pagination (only when fetch_all=False).
            fetch_all: If True, fetches all pages automatically.
                       If False (default), returns raw result for one page.

        Returns:
            If fetch_all=True: List of all candidate products.
            If fetch_all=False: Raw result dict with 'products', 'total', 'last_id'.

        Raises:
            OzonPromotionError: If API returns an error.
        """
        if not fetch_all:
            body: dict[str, Any] = {"action_id": action_id, "limit": limit}
            if last_id:
                body["last_id"] = last_id
            response = await self._client.post(SellerEndpoints.ACTIONS_CANDIDATES, body)
            self._check_error(response)
            return response.get("result", {})

        all_products: APIItemsList = []
        current_last_id: str = ""

        while True:
            body = {"action_id": action_id, "limit": limit}
            if current_last_id:
                body["last_id"] = current_last_id

            response = await self._client.post(SellerEndpoints.ACTIONS_CANDIDATES, body)
            self._check_error(response)
            result = response.get("result", {})
            products = result.get("products", [])
            all_products.extend(products)

            current_last_id = result.get("last_id", "")
            if not current_last_id or not products:
                break

        return all_products

    async def get_products(
        self,
        action_id: int,
        limit: int = 100,
        last_id: str = "",
        fetch_all: bool = False,
    ) -> APIItemsList | APIResult:
        """Fetch products currently participating in a promotion.

        Args:
            action_id: Promotion ID from get_actions().
            limit: Results per page (default: 100).
            last_id: Last item ID for pagination (only when fetch_all=False).
            fetch_all: If True, fetches all pages automatically.
                       If False (default), returns raw result for one page.

        Returns:
            If fetch_all=True: List of all participating products.
            If fetch_all=False: Raw result dict with 'products', 'total', 'last_id'.

        Raises:
            OzonPromotionError: If API returns an error.
        """
        if not fetch_all:
            body: dict[str, Any] = {"action_id": action_id, "limit": limit}
            if last_id:
                body["last_id"] = last_id
            response = await self._client.post(SellerEndpoints.ACTIONS_PRODUCTS, body)
            self._check_error(response)
            return response.get("result", {})

        all_products: APIItemsList = []
        current_last_id: str = ""

        while True:
            body = {"action_id": action_id, "limit": limit}
            if current_last_id:
                body["last_id"] = current_last_id

            response = await self._client.post(SellerEndpoints.ACTIONS_PRODUCTS, body)
            self._check_error(response)
            result = response.get("result", {})
            products = result.get("products", [])
            all_products.extend(products)

            current_last_id = result.get("last_id", "")
            if not current_last_id or not products:
                break

        return all_products

    async def activate_products(
        self,
        action_id: int,
        products: list[ActivateProduct],
    ) -> APIResult:
        """Add products to a promotion.

        Args:
            action_id: Promotion ID from get_actions().
            products: List of ActivateProduct dicts (max 1000).

        Returns:
            Result dict with 'product_ids' (added) and 'rejected' lists.

        Raises:
            OzonPromotionError: If API returns an error.
        """
        body = {"action_id": action_id, "products": products}
        response = await self._client.post(SellerEndpoints.ACTIONS_PRODUCTS_ACTIVATE, body)
        self._check_error(response)
        return response.get("result", {})

    async def deactivate_products(
        self,
        action_id: int,
        product_ids: list[int],
    ) -> APIResult:
        """Remove products from a promotion.

        Args:
            action_id: Promotion ID from get_actions().
            product_ids: List of product IDs to remove.

        Returns:
            Result dict with 'product_ids' (removed) and 'rejected' lists.

        Raises:
            OzonPromotionError: If API returns an error.
        """
        body = {"action_id": action_id, "product_ids": product_ids}
        response = await self._client.post(SellerEndpoints.ACTIONS_PRODUCTS_DEACTIVATE, body)
        self._check_error(response)
        return response.get("result", {})
