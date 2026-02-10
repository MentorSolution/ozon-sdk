import pytest

from ozon_api_sdk.constants import ProductVisibility

pytestmark = pytest.mark.integration


async def test_get_products_by_visibility(seller_client, save_response):
    products = await seller_client.products.get_products_by_visibility(
        visibility=ProductVisibility.ALL, limit=10
    )
    save_response(products)
    assert isinstance(products, list)


async def test_get_products(seller_client, save_response):
    products = await seller_client.products.get_products(
        visibilities=[ProductVisibility.ALL]
    )
    save_response(products)
    assert isinstance(products, list)


async def test_get_product_info(seller_client, save_response):
    products = await seller_client.products.get_products_by_visibility(limit=1)
    if not products:
        pytest.skip("No products found in account")

    offer_id = products[0].get("offer_id")
    result = await seller_client.products.get_product_info(offer_ids=[offer_id])
    save_response(result)
    assert isinstance(result, list)
