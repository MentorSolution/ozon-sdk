from datetime import datetime, timedelta

import pytest

pytestmark = pytest.mark.integration


async def test_get_transactions(seller_client, save_response):
    date_to = datetime.now()
    date_from = date_to - timedelta(days=7)

    result = await seller_client.finance.get_transactions(
        date_from=date_from, date_to=date_to
    )
    save_response(result)
    assert isinstance(result, dict)
    assert "operations" in result


async def test_get_transaction_totals(seller_client, save_response):
    date_to = datetime.now()
    date_from = date_to - timedelta(days=7)

    result = await seller_client.finance.get_transaction_totals(
        date_from=date_from, date_to=date_to
    )
    save_response(result)
    assert isinstance(result, dict)
