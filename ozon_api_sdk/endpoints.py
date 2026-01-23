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
    PRODUCT_LIST = "/v2/product/list"
    PRODUCT_INFO_LIST = "/v2/product/info/list"
    GENERATE_PRODUCT_TO_CSV = "/v1/product/list/csv"
    GET_PRODUCT_TO_CSV = "/v1/product/list/csv/info"

    # Finance
    TRANSACTION_LIST = "/v3/finance/transaction/list"
    TRANSACTION_TOTALS = "/v3/finance/transaction/totals"


class PerformanceEndpoints:
    """Performance API endpoint URLs."""

    # Campaigns
    CLIENT_CAMPAIGN = "/api/client/campaign"
    STATISTICS = "/api/client/statistics"
    STATISTICS_REPORT = "/api/client/statistics/report"
    STATISTICS_REPORT_STATUS = "/api/client/statistics/"
