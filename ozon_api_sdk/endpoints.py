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

    # Products
    PRODUCT_LIST = "/v3/product/list"
    PRODUCT_INFO_LIST = "/v3/product/info/list"

    # Finance
    TRANSACTION_LIST = "/v3/finance/transaction/list"
    TRANSACTION_TOTALS = "/v3/finance/transaction/totals"

    # Promotions
    ACTIONS_LIST = "/v1/actions"
    ACTIONS_CANDIDATES = "/v1/actions/candidates"
    ACTIONS_PRODUCTS = "/v1/actions/products"
    ACTIONS_PRODUCTS_ACTIVATE = "/v1/actions/products/activate"
    ACTIONS_PRODUCTS_DEACTIVATE = "/v1/actions/products/deactivate"


class PerformanceEndpoints:
    """Performance API endpoint URLs."""

    # Campaigns
    CLIENT_CAMPAIGN = "/api/client/campaign"
    STATISTICS = "/api/client/statistics"
    STATISTICS_REPORT = "/api/client/statistics/report"
    STATISTICS_REPORT_STATUS = "/api/client/statistics/"
