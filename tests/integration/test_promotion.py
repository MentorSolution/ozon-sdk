import pytest

pytestmark = [pytest.mark.integration, pytest.mark.seller]


async def test_get_actions(seller_client, save_response):
    actions = await seller_client.promotion.get_actions()
    save_response(actions)
    assert isinstance(actions, list)


async def test_get_candidates(seller_client, save_response):
    actions = await seller_client.promotion.get_actions()
    if not actions:
        pytest.skip("No promotions found in account")

    action_id = actions[0]["id"]
    result = await seller_client.promotion.get_candidates(action_id=action_id)
    save_response(result)
    assert isinstance(result, dict)


async def test_get_products(seller_client, save_response):
    actions = await seller_client.promotion.get_actions()
    if not actions:
        pytest.skip("No promotions found in account")

    action_id = actions[0]["id"]
    result = await seller_client.promotion.get_products(action_id=action_id)
    save_response(result)
    assert isinstance(result, dict)
