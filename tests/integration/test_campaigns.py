from datetime import datetime, timedelta

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.performance]


async def test_get_campaigns(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    save_response(campaigns)
    assert isinstance(campaigns, list)


async def test_get_campaign_by_id(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    if not campaigns:
        pytest.skip("No campaigns found in account")

    campaign_id = str(campaigns[0]["id"])
    result = await performance_client.campaigns.get_campaign_by_id(campaign_id)
    save_response(result)
    assert isinstance(result, dict)


async def test_get_statistics_report(performance_client, save_response):
    campaigns = await performance_client.campaigns.get_campaigns()
    if not campaigns:
        pytest.skip("No campaigns found in account")

    campaign_id = str(campaigns[0]["id"])
    date_to = datetime.now()
    date_from = date_to - timedelta(days=7)

    result = await performance_client.campaigns.get_statistics_report(
        campaign_ids=[campaign_id],
        date_from=date_from,
        date_to=date_to,
        max_attempts=10,
        poll_interval=5.0,
    )
    save_response(result)
    assert isinstance(result, dict)
