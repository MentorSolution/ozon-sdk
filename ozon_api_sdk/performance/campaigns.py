from __future__ import annotations

import asyncio
import csv
import io
import time
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from ozon_api_sdk.base import ReportPollingProgress
from ozon_api_sdk.constants import AdvertisingType, CampaignState, StatisticsGroupBy
from ozon_api_sdk.endpoints import PerformanceEndpoints

if TYPE_CHECKING:
    from ozon_api_sdk.performance.client import PerformanceAPIClient

ProgressCallback = Callable[[ReportPollingProgress], None]

class CampaignsAPI:
    """Campaigns API subclient for Performance API."""

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
            adv_types = (AdvertisingType.SKU, AdvertisingType.SEARCH_PROMO)

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
        adv_object_type: str = AdvertisingType.SKU,
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
            "state": CampaignState.UNKNOWN,
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
        group_by: str = StatisticsGroupBy.DATE,
        max_attempts: int = 30,
        poll_interval: float = 10.0,
        on_progress: ProgressCallback | None = None,
    ) -> list[dict[str, Any]]:
        """Request statistics report, poll for completion, and return CSV data.

        Performance API report generation is asynchronous - this method handles
        the full lifecycle: request → poll → download.

        Note: CSV reports are automatically parsed to JSON format.
        Ozon API returns different formats based on campaign count:
            - CSV text (single campaign) → automatically parsed
            - ZIP archive (multiple campaigns) → each CSV extracted and parsed

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
            List of campaign reports:
                [
                    {
                        "campaign_id": "123",
                        "campaign_header": "; Кампания по продвижению товаров № 123...",
                        "data": [
                            {"sku": "...", "Название товара": "...", "Показы": "100", ...},
                            ...
                        ]
                    },
                    {
                        "campaign_id": "456",
                        "campaign_header": "...",
                        "data": [...]
                    }
                ]

        Raises:
            ValueError: If campaign_ids > 10 or report generation fails.
            TimeoutError: If report not ready after max_attempts.

        Example:
            report = await client.campaigns.get_statistics_report(
                campaign_ids=["123", "456"],
                date_from=datetime(2024, 1, 1),
                date_to=datetime(2024, 1, 31),
            )

            # Iterate through campaigns
            for campaign in report:
                campaign_id = campaign["campaign_id"]
                rows = campaign["data"]
                print(f"Campaign {campaign_id}: {len(rows)} rows")

                for row in rows:
                    print(f"  SKU: {row['sku']}, Показы: {row['Показы']}, Клики: {row['Клики']}")

            # Or access specific campaign
            campaign_123 = next(c for c in report if c["campaign_id"] == "123")
            total_shows = sum(int(row.get("Показы", 0) or 0) for row in campaign_123["data"])
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
                return await self._download_report(report_uuid, campaign_ids)

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

    @staticmethod
    def _parse_csv_to_json(csv_text: str, campaign_id: str | None = None) -> dict[str, Any]:
        """Parse Ozon CSV report to JSON format.

        Args:
            csv_text: CSV content as string.
            campaign_id: Campaign ID for this report.

        Returns:
            Dict with campaign data and parsed rows.
        """
        lines = csv_text.strip().split("\n")

        # Первая строка - заголовок кампании (начинается с ;)
        campaign_header = lines[0].strip() if lines else ""

        # Вторая строка - названия колонок
        if len(lines) < 2:
            return {"campaign_id": campaign_id, "header": campaign_header, "data": []}

        # Парсим CSV с разделителем ;
        reader = csv.DictReader(
            io.StringIO("\n".join(lines[1:])),  # Пропускаем первую строку
            delimiter=";",
        )

        rows = []
        for row in reader:
            # Очищаем пробелы в ключах и значениях
            cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
            rows.append(cleaned_row)

        return {
            "campaign_id": campaign_id,
            "campaign_header": campaign_header,
            "data": rows,
        }

    async def _download_report(
        self, report_uuid: str, campaign_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Download completed report and parse to JSON.

        Performance API returns different formats:
        - CSV text if single campaign
        - ZIP archive if multiple campaigns

        Args:
            report_uuid: Report UUID from API.
            campaign_ids: List of campaign IDs from request.

        Returns:
            List of campaign reports:
                [
                    {"campaign_id": "123", "campaign_header": "...", "data": [...]},
                    {"campaign_id": "456", "campaign_header": "...", "data": [...]},
                ]
        """
        response = await self._client._request_raw(
            "GET",
            PerformanceEndpoints.STATISTICS_REPORT,
            params={"UUID": report_uuid},
        )

        content_type = response.headers.get("content-type", "").lower()
        campaigns_list: list[dict[str, Any]] = []

        if "zip" in content_type or "application/zip" in content_type:
            # ZIP архив - распаковать и парсить каждый CSV
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                for filename in zf.namelist():
                    # Имя файла: "123.csv" → campaign_id: "123"
                    campaign_id = filename.replace(".csv", "")
                    csv_bytes = zf.read(filename)
                    csv_text = csv_bytes.decode("utf-8")

                    campaigns_list.append(self._parse_csv_to_json(csv_text, campaign_id))
        else:
            # CSV текст - используем первый campaign_id из запроса
            csv_text = response.text
            campaign_id = campaign_ids[0] if campaign_ids else "unknown"
            parsed = self._parse_csv_to_json(csv_text, campaign_id)

            campaigns_list.append(parsed)

        return campaigns_list

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
