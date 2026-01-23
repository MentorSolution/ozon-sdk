"""Ozon API endpoint URL constants.

Usage:
    from ozon_api_sdk.endpoints import SellerEndpoints, PerformanceEndpoints

    await client.post(SellerEndpoints.PRODUCT_LIST, {"limit": 100})

Adding new endpoints:
    class SellerEndpoints:
        PRODUCT_LIST = "/v2/product/list"
        PRODUCT_INFO = "/v2/product/info"
        WAREHOUSE_LIST = "/v1/warehouse/list"

Docs:
    Seller API: https://docs.ozon.ru/api/seller/
    Performance API: https://docs.ozon.ru/api/performance/
"""


class SellerEndpoints:
    """Seller API endpoint URLs."""

    pass


class PerformanceEndpoints:
    """Performance API endpoint URLs."""

    pass
