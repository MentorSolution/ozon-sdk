from __future__ import annotations

import asyncio
from itertools import batched
from typing import TYPE_CHECKING, Any, Sequence

from ozon_api_sdk.constants import ProductVisibility
from ozon_api_sdk.endpoints import SellerEndpoints

if TYPE_CHECKING:
    from ozon_api_sdk.seller.client import SellerAPIClient


class ProductsAPI:
    """Products API subclient for Seller API."""

    PRODUCT_LIST_LIMIT = 1000
    PRODUCT_INFO_BATCH_SIZE = 1000

    def __init__(self, client: SellerAPIClient) -> None:
        self._client = client

    async def get_products_by_visibility(
        self,
        visibility: str = ProductVisibility.ALL,
        limit: int = PRODUCT_LIST_LIMIT,
    ) -> list[dict[str, Any]]:
        """Fetch all products with specified visibility filter.

        Handles pagination automatically.

        Args:
            visibility: Product visibility filter (default: ALL).
            limit: Products per request (default: 1000).

        Returns:
            List of product dictionaries with product_id, offer_id, is_fbo_visible, is_fbs_visible.
        """
        all_items: list[dict[str, Any]] = []
        last_id: str | None = None

        while True:
            body: dict[str, Any] = {
                "filter": {"visibility": visibility},
                "limit": limit,
            }
            if last_id:
                body["last_id"] = last_id

            response = await self._client.post(SellerEndpoints.PRODUCT_LIST, body)
            result = response.get("result", {})
            items = result.get("items", [])
            all_items.extend(items)

            last_id = result.get("last_id")
            if not last_id or last_id == "":
                break

        return all_items

    async def get_products(
        self,
        visibilities: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch products from multiple visibility filters.

        Args:
            visibilities: List of visibility filters.
                         Default: [ALL, ARCHIVED, INVISIBLE].

        Returns:
            Combined list of products from all visibility filters.
        """
        if visibilities is None:
            visibilities = [
                ProductVisibility.ALL,
                ProductVisibility.ARCHIVED,
                ProductVisibility.INVISIBLE,
            ]

        results = await asyncio.gather(
            *[self.get_products_by_visibility(v) for v in visibilities]
        )

        all_items: list[dict[str, Any]] = []
        for result in results:
            all_items.extend(result)

        return all_items

    async def get_product_info(
        self,
        offer_ids: Sequence[str],
        batch_size: int = PRODUCT_INFO_BATCH_SIZE,
    ) -> list[dict[str, Any]]:
        """Fetch detailed product info by offer IDs.

        Handles batching automatically for large lists.

        Args:
            offer_ids: List of offer IDs to fetch.
            batch_size: Number of IDs per request (default: 1000).

        Returns:
            List of product info dictionaries.
        """
        all_items: list[dict[str, Any]] = []

        for batch in batched(offer_ids, batch_size):
            response = await self._client.post(
                SellerEndpoints.PRODUCT_INFO_LIST,
                {"offer_id": list(batch)},
            )
            items = response.get("items", [])
            all_items.extend(items)

        return all_items
