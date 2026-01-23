from __future__ import annotations

import asyncio
from itertools import batched
from typing import TYPE_CHECKING, Any, Sequence

import httpx

from ozon_api_sdk.endpoints import SellerEndpoints

if TYPE_CHECKING:
    from ozon_api_sdk.seller.client import SellerAPIClient


class ProductsAPI:
    """Products API subclient for Seller API."""

    # Product visibility filters
    VISIBILITY_ALL = "ALL"
    VISIBILITY_VISIBLE = "VISIBLE"
    VISIBILITY_INVISIBLE = "INVISIBLE"
    VISIBILITY_EMPTY_STOCK = "EMPTY_STOCK"
    VISIBILITY_NOT_MODERATED = "NOT_MODERATED"
    VISIBILITY_MODERATED = "MODERATED"
    VISIBILITY_DISABLED = "DISABLED"
    VISIBILITY_STATE_FAILED = "STATE_FAILED"
    VISIBILITY_READY_TO_SUPPLY = "READY_TO_SUPPLY"
    VISIBILITY_VALIDATION_STATE_PENDING = "VALIDATION_STATE_PENDING"
    VISIBILITY_VALIDATION_STATE_FAIL = "VALIDATION_STATE_FAIL"
    VISIBILITY_VALIDATION_STATE_SUCCESS = "VALIDATION_STATE_SUCCESS"
    VISIBILITY_TO_SUPPLY = "TO_SUPPLY"
    VISIBILITY_IN_SALE = "IN_SALE"
    VISIBILITY_REMOVED_FROM_SALE = "REMOVED_FROM_SALE"
    VISIBILITY_BANNED = "BANNED"
    VISIBILITY_OVERPRICED = "OVERPRICED"
    VISIBILITY_CRITICALLY_OVERPRICED = "CRITICALLY_OVERPRICED"
    VISIBILITY_EMPTY_BARCODE = "EMPTY_BARCODE"
    VISIBILITY_BARCODE_EXISTS = "BARCODE_EXISTS"
    VISIBILITY_QUARANTINE = "QUARANTINE"
    VISIBILITY_ARCHIVED = "ARCHIVED"
    VISIBILITY_OVERPRICED_WITH_STOCK = "OVERPRICED_WITH_STOCK"
    VISIBILITY_PARTIAL_APPROVED = "PARTIAL_APPROVED"
    VISIBILITY_IMAGE_ABSENT = "IMAGE_ABSENT"
    VISIBILITY_MODERATION_BLOCK = "MODERATION_BLOCK"

    # Request limits
    PRODUCT_LIST_LIMIT = 1000
    PRODUCT_INFO_BATCH_SIZE = 1000

    def __init__(self, client: SellerAPIClient) -> None:
        self._client = client

    async def get_products_by_visibility(
        self,
        visibility: str = VISIBILITY_ALL,
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
                self.VISIBILITY_ALL,
                self.VISIBILITY_ARCHIVED,
                self.VISIBILITY_INVISIBLE,
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

    async def get_product_csv_report(
        self,
        search: str = "",
        sku: list[int] | None = None,
        offer_id: list[str] | None = None,
        visibility: str | Sequence[str] = VISIBILITY_ALL,
        language: str = "DEFAULT",
        max_attempts: int = 10,
        poll_interval: float = 1.0,
    ) -> str:
        """Generate and download product CSV report.

        Args:
            search: Search text to filter products.
            sku: List of product SKUs to filter.
            offer_id: List of offer IDs to filter.
            visibility: Single visibility filter or list of filters.
            language: Language for product data (default: DEFAULT).
            max_attempts: Max polling attempts (default: 10).
            poll_interval: Seconds between polls (default: 1.0).

        Returns:
            Combined CSV content as string.

        Raises:
            ValueError: If report generation fails.
            TimeoutError: If report not ready after max_attempts.
        """
        if isinstance(visibility, str):
            visibilities = [visibility]
        else:
            visibilities = list(visibility)

        all_csv_contents: list[str] = []
        csv_header: str | None = None

        for vis in visibilities:
            body = {
                "language": language,
                "offer_id": offer_id or [],
                "search": search,
                "sku": sku or [],
                "visibility": vis,
            }

            csv_content = await self._fetch_csv_report(
                body, max_attempts, poll_interval
            )

            lines = csv_content.strip().split("\n")
            if not lines:
                continue

            if csv_header is None:
                csv_header = lines[0]
                all_csv_contents.append(csv_content)
            else:
                if len(lines) > 1:
                    data_rows = "\n".join(lines[1:])
                    all_csv_contents.append(data_rows)

        if not all_csv_contents:
            return ""

        return "\n".join(all_csv_contents)

    async def _fetch_csv_report(
        self,
        body: dict[str, Any],
        max_attempts: int,
        poll_interval: float,
    ) -> str:
        """Internal: Request CSV report, poll for completion, download."""
        response = await self._client.post(
            SellerEndpoints.GENERATE_PRODUCT_TO_CSV, body
        )
        result = response.get("result", {})
        report_code = result.get("code")

        if not report_code:
            raise ValueError("Report code not found in API response")

        for _ in range(max_attempts):
            response = await self._client.post(
                SellerEndpoints.GET_PRODUCT_TO_CSV,
                {"code": report_code},
            )
            result = response.get("result", {})

            if result.get("status") == "success":
                if result.get("error"):
                    raise ValueError(f"Error generating file: {result['error']}")

                file_url = result.get("file")
                if not file_url:
                    raise ValueError("File URL not found in API response")

                async with httpx.AsyncClient() as http_client:
                    csv_response = await http_client.get(file_url)
                    csv_response.raise_for_status()
                    return csv_response.text

            await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"Report not ready after {max_attempts} attempts "
            f"({max_attempts * poll_interval} seconds)"
        )
