from datetime import datetime, timedelta

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.seller]


async def test_get_analytics_data(seller_client, save_response):
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=7)

    result = await seller_client.analytics.get_analytics_data(
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        dimension=["day", "sku"],
        metrics=["ordered_units", "revenue"],
    )

    save_response(result)
    assert isinstance(result, list)
    if result:
        assert isinstance(result[0], dict)
