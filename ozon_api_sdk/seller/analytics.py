from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, List, Any

from ozon_api_sdk.endpoints import SellerEndpoints
from ozon_api_sdk.constants import Dimension, Metrics

if TYPE_CHECKING:
    from ozon_api_sdk.seller.client import SellerAPIClient


class AnalyticsAPI:
    """AnalyticsAPI API subclient for Seller API."""

    ANALYTICS_DATA_LIMIT = 1000

    def __init__(self, client: SellerAPIClient) -> None:
        self._client = client

    async def get_analytics_data(
        self,
        date_from: str,
        date_to: str,
        dimension: List[Dimension],
        metrics: List[Metrics],
        limit: int = ANALYTICS_DATA_LIMIT
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        offset: int = 0

        while True:
            body: dict[str, Any] = {
                "date_from": date_from,
                "date_to": date_to,
                "dimension": dimension,
                "metrics": metrics,
                "offset": offset,
                "limit": limit
            }

            response = await self._client.post(SellerEndpoints.ANALYTICS_DATA, body)
            result = response.get("result", {})
            data = result.get("data", [])

            if len(data) == 0:
                break

            offset += len(data)

            for _d in data:
                _row = {}

                _dimensions = _d['dimensions']
                _metrics = _d['metrics']

                for i, dim in enumerate(_dimensions):
                    _row[dimension[i]] = dim['id']

                for i, met in enumerate(_metrics):
                    _row[metrics[i]] = met

                all_items.append(_row)

            await asyncio.sleep(60)

        return all_items
