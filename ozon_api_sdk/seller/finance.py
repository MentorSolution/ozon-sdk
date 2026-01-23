from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from ozon_api_sdk.endpoints import SellerEndpoints

if TYPE_CHECKING:
    from ozon_api_sdk.seller.client import SellerAPIClient


class FinanceAPI:
    """Finance API subclient for Seller API."""

    TRANSACTION_LIST_LIMIT = 1000

    def __init__(self, client: SellerAPIClient) -> None:
        self._client = client

    async def get_transactions(
        self,
        date_from: datetime,
        date_to: datetime,
        operation_types: list[str] | None = None,
        posting_number: str = "",
        transaction_type: str = "all",
        page_size: int = TRANSACTION_LIST_LIMIT,
    ) -> dict[str, Any]:
        """Fetch transactions for the specified period.

        Automatically splits period into monthly intervals and handles pagination.

        Args:
            date_from: Start date.
            date_to: End date.
            operation_types: Filter by operation types (default: all).
            posting_number: Filter by posting number.
            transaction_type: Filter type: "all", "orders", "returns", etc.
            page_size: Transactions per page (default: 1000).

        Returns:
            Dict with:
                - "operations": list of transaction operations
                - "errors": list of date ranges with errors (if any)
        """
        all_operations: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        date_ranges = self._split_into_monthly_ranges(date_from, date_to)

        for range_start, range_end in date_ranges:
            try:
                operations = await self._fetch_transactions_for_range(
                    range_start,
                    range_end,
                    operation_types,
                    posting_number,
                    transaction_type,
                    page_size,
                )
                all_operations.extend(operations)
            except Exception as e:
                errors.append(
                    {
                        "date_from": range_start.isoformat(),
                        "date_to": range_end.isoformat(),
                        "error": f"{type(e).__name__}: {str(e)}",
                    }
                )

        return {"operations": all_operations, "errors": errors}

    async def _fetch_transactions_for_range(
        self,
        date_from: datetime,
        date_to: datetime,
        operation_types: list[str] | None,
        posting_number: str,
        transaction_type: str,
        page_size: int,
    ) -> list[dict[str, Any]]:
        """Fetch all transactions for a single date range with pagination."""
        all_operations: list[dict[str, Any]] = []
        page = 1

        while True:
            body = {
                "filter": {
                    "date": {
                        "from": self._datetime_to_start_of_day_iso(date_from),
                        "to": self._datetime_to_end_of_day_iso(date_to),
                    },
                    "operation_type": operation_types or [],
                    "posting_number": posting_number,
                    "transaction_type": transaction_type,
                },
                "page": page,
                "page_size": page_size,
            }

            response = await self._client.post(
                SellerEndpoints.TRANSACTION_LIST, body
            )
            result = response.get("result", {})
            operations = result.get("operations", [])
            all_operations.extend(operations)

            page_count = result.get("page_count", 1)
            if page >= page_count:
                break

            page += 1

        return all_operations

    async def get_transaction_totals(
        self,
        date_from: datetime,
        date_to: datetime,
        transaction_type: str = "all",
    ) -> dict[str, Any]:
        """Get financial transaction totals for a specified period.

        Args:
            date_from: Start date.
            date_to: End date.
            transaction_type: Filter type: "all", "orders", "returns", etc.

        Returns:
            Financial summary with totals.
        """
        body = {
            "date": {
                "from": self._datetime_to_start_of_day_iso(date_from),
                "to": self._datetime_to_end_of_day_iso(date_to),
            },
            "transaction_type": transaction_type,
        }

        response = await self._client.post(SellerEndpoints.TRANSACTION_TOTALS, body)
        return response.get("result", {})

    def _split_into_monthly_ranges(
        self, date_from: datetime, date_to: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Split date range into monthly intervals (if > 31 days)."""
        if (date_to - date_from).days <= 31:
            return [(date_from, date_to)]

        ranges: list[tuple[datetime, datetime]] = []
        current_start = date_from

        while current_start < date_to:
            if current_start.month == 12:
                next_month = current_start.replace(
                    year=current_start.year + 1, month=1
                )
            else:
                next_month = current_start.replace(month=current_start.month + 1)

            current_end = min(next_month, date_to)
            ranges.append((current_start, current_end))
            current_start = current_end

        return ranges

    @staticmethod
    def _datetime_to_start_of_day_iso(dt: datetime) -> str:
        """Convert datetime to ISO string at start of day."""
        return dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"

    @staticmethod
    def _datetime_to_end_of_day_iso(dt: datetime) -> str:
        """Convert datetime to ISO string at end of day."""
        return (
            dt.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
            + "Z"
        )
