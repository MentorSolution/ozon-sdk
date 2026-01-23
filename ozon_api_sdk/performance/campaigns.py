from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from ozon_api_sdk.base import ReportPollingProgress
from ozon_api_sdk.endpoints import PerformanceEndpoints

if TYPE_CHECKING:
    from ozon_api_sdk.performance.client import PerformanceAPIClient

# Type alias for progress callback
ProgressCallback = Callable[[ReportPollingProgress], None]


class CampaignsAPI:
    """Campaigns API subclient for Performance API."""

    # Campaign states
    STATE_UNKNOWN = "CAMPAIGN_STATE_UNKNOWN"
    STATE_RUNNING = "CAMPAIGN_STATE_RUNNING"
    STATE_PLANNED = "CAMPAIGN_STATE_PLANNED"
    STATE_STOPPED = "CAMPAIGN_STATE_STOPPED"
    STATE_INACTIVE = "CAMPAIGN_STATE_INACTIVE"
    STATE_ARCHIVED = "CAMPAIGN_STATE_ARCHIVED"
    STATE_MODERATION_DRAFT = "CAMPAIGN_STATE_MODERATION_DRAFT"
    STATE_MODERATION_IN_PROGRESS = "CAMPAIGN_STATE_MODERATION_IN_PROGRESS"
    STATE_MODERATION_FAILED = "CAMPAIGN_STATE_MODERATION_FAILED"
    STATE_FINISHED = "CAMPAIGN_STATE_FINISHED"

    # Advertising object types
    ADV_TYPE_SKU = "SKU"
    ADV_TYPE_SEARCH_PROMO = "SEARCH_PROMO"
    ADV_TYPE_BANNER = "BANNER"
    ADV_TYPE_BRAND_SHELF = "BRAND_SHELF"
    ADV_TYPE_VIDEO = "VIDEO"

    # Payment types
    PAYMENT_CPC = "CPC"
    PAYMENT_CPM = "CPM"
    PAYMENT_CPO = "CPO"

    # Group by options for statistics
    GROUP_BY_DATE = "DATE"
    GROUP_BY_NO_GROUP_BY = "NO_GROUP_BY"
    GROUP_BY_START_OF_WEEK = "START_OF_WEEK"
    GROUP_BY_START_OF_MONTH = "START_OF_MONTH"

    def __init__(self, client: PerformanceAPIClient) -> None:
        self._client = client

    async def get_campaigns(
        self,
        campaign_ids: list[str] | None = None,
        adv_types: tuple[str, ...] | None = None,
        payment_types: tuple[str, ...] | None = None,
        page_size: int = 100,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch advertising campaigns with filtering.

        Handles pagination automatically.

        Args:
            campaign_ids: Filter by campaign IDs (default: all).
            adv_types: Filter by advertising types (default: SKU, SEARCH_PROMO).
            payment_types: Filter by payment types (default: all).
            page_size: Campaigns per page (default: 100).
            max_pages: Max pages to fetch (default: 100).

        Returns:
            List of campaign dictionaries.
        """
        if adv_types is None:
            adv_types = (self.ADV_TYPE_SKU, self.ADV_TYPE_SEARCH_PROMO)

        page = 1
        result: list[dict[str, Any]] = []
        seen_campaign_ids: set[str] = set()

        while page <= max_pages:
            params = {
                "campaignIds": campaign_ids or [],
                "page": page,
                "pageSize": page_size,
                "advObjectType": "",
            }

            response = await self._client.get(
                PerformanceEndpoints.CLIENT_CAMPAIGN,
                params=params,
            )
            campaigns_list = response.get("list", [])

            if not campaigns_list:
                break

            new_campaigns_on_page = 0

            for camp in campaigns_list:
                camp_id = str(camp["id"])

                if camp_id in seen_campaign_ids:
                    continue
                seen_campaign_ids.add(camp_id)
                new_campaigns_on_page += 1

                adv_type = camp.get("advObjectType")
                payment_type = camp.get("PaymentType")

                if adv_type not in adv_types:
                    continue

                if payment_types is not None and payment_type not in payment_types:
                    continue

                result.append(camp)

            if new_campaigns_on_page == 0:
                break

            if len(campaigns_list) < page_size:
                break

            page += 1

        return result

    async def get_campaign_by_id(
        self,
        campaign_id: str,
        adv_object_type: str = ADV_TYPE_SKU,
    ) -> dict[str, Any]:
        """Fetch single campaign by ID.

        Args:
            campaign_id: Campaign ID.
            adv_object_type: Type of advertising object (default: SKU).

        Returns:
            Campaign data dictionary.

        Raises:
            ValueError: If campaign not found.
        """
        params = {
            "campaignIds": [campaign_id],
            "advObjectType": adv_object_type,
            "state": self.STATE_UNKNOWN,
        }

        response = await self._client.get(
            PerformanceEndpoints.CLIENT_CAMPAIGN,
            params=params,
        )

        campaigns = response.get("list", [])
        if not campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        return campaigns[0]

    async def get_statistics_report(
        self,
        campaign_ids: list[str],
        date_from: datetime,
        date_to: datetime,
        group_by: str = GROUP_BY_DATE,
        max_attempts: int = 30,
        poll_interval: float = 10.0,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Request statistics report, poll for completion, and return data.

        Performance API report generation is asynchronous - this method handles
        the full lifecycle: request → poll → download.

        Args:
            campaign_ids: List of campaign IDs (max 10).
            date_from: Start date.
            date_to: End date.
            group_by: Grouping parameter (default: DATE).
            max_attempts: Max polling attempts (default: 30).
            poll_interval: Seconds between polls (default: 10.0).
            on_progress: Optional callback called on each poll with ReportPollingProgress.
                        Use this to track progress, log status, or update UI.

        Returns:
            Statistics report data.

        Raises:
            ValueError: If campaign_ids > 10 or report generation fails.
            TimeoutError: If report not ready after max_attempts.

        Example:
            def progress_handler(progress: ReportPollingProgress):
                print(f"Polling: {progress}")  # or log, update progress bar, etc.

            report = await client.campaigns.get_statistics_report(
                campaign_ids=["123"],
                date_from=datetime(2024, 1, 1),
                date_to=datetime(2024, 1, 31),
                on_progress=progress_handler,
            )
        """
        if len(campaign_ids) > 10:
            raise ValueError(f"campaign_ids > 10. Got {len(campaign_ids)}")

        report_uuid = await self._request_statistics_report(
            campaign_ids, date_from, date_to, group_by
        )

        if not report_uuid:
            raise ValueError("Report UUID not found in API response")

        start_time = time.monotonic()
        status: str | None = None

        for attempt in range(max_attempts):
            status = await self._get_report_status(report_uuid)
            elapsed = time.monotonic() - start_time
            is_last_attempt = attempt >= max_attempts - 1
            next_poll = None if is_last_attempt else poll_interval

            # Call progress callback
            if on_progress:
                progress = ReportPollingProgress(
                    report_uuid=report_uuid,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    status=status,
                    elapsed_seconds=elapsed,
                    next_poll_in=next_poll,
                )
                on_progress(progress)

            if status == "OK":
                return await self._download_report(report_uuid)

            if not is_last_attempt:
                await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"Report {report_uuid} not ready after {max_attempts} attempts "
            f"({time.monotonic() - start_time:.1f} seconds). Last status: {status}"
        )

    async def _request_statistics_report(
        self,
        campaign_ids: list[str],
        date_from: datetime,
        date_to: datetime,
        group_by: str,
    ) -> str | None:
        """Request statistics report generation."""
        body = {
            "campaigns": campaign_ids,
            "from": self._datetime_to_start_of_day_iso(date_from),
            "to": self._datetime_to_end_of_day_iso(date_to),
            "groupBy": group_by,
        }

        response = await self._client.post(PerformanceEndpoints.STATISTICS, body)
        return response.get("UUID")

    async def _get_report_status(self, report_uuid: str) -> str | None:
        """Check report generation status."""
        url = f"{PerformanceEndpoints.STATISTICS_REPORT_STATUS}{report_uuid}"
        response = await self._client.get(url)
        return response.get("state")

    async def _download_report(self, report_uuid: str) -> dict[str, Any]:
        """Download completed report."""
        return await self._client.get(
            PerformanceEndpoints.STATISTICS_REPORT,
            params={"UUID": report_uuid},
        )

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
