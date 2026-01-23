import asyncio
from datetime import datetime, timedelta

from ozon_api_sdk import (
    SellerAPIClient,
    PerformanceAPIClient,
    SellerEndpoints,
    PerformanceEndpoints,
    RetryConfig,
    ReportPollingProgress,
)


async def seller_example():
    """Example: Seller API usage with subclients."""
    async with SellerAPIClient(
        client_id=123456,
        api_key="your-api-key",
    ) as client:
        # Via subclient: get all products
        products = await client.products.get_products()
        print(f"Products: {len(products)}")

        # Via subclient: get product info by offer IDs
        if products:
            offer_ids = [p["offer_id"] for p in products[:10]]
            product_info = await client.products.get_product_info(offer_ids)
            print(f"Product info: {len(product_info)}")

        # Via subclient: get transactions
        date_from = datetime.now() - timedelta(days=30)
        date_to = datetime.now()
        transactions = await client.finance.get_transactions(date_from, date_to)
        print(f"Transactions: {len(transactions['operations'])}")

        # Direct API call (still available)
        response = await client.post(SellerEndpoints.PRODUCT_LIST, {
            "filter": {},
            "limit": 10,
        })
        print(f"Direct call: {len(response.get('result', {}).get('items', []))} items")


async def performance_example():
    """Example: Performance API usage with subclients."""
    async with PerformanceAPIClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
    ) as client:
        # Via subclient: get campaigns
        campaigns = await client.campaigns.get_campaigns()
        print(f"Campaigns: {len(campaigns)}")

        # Via subclient: get statistics report
        if campaigns:
            campaign_ids = [str(c["id"]) for c in campaigns[:5]]
            date_from = datetime.now() - timedelta(days=7)
            date_to = datetime.now()
            report = await client.campaigns.get_statistics_report(
                campaign_ids, date_from, date_to
            )
            print(f"Statistics report: {report}")

        # Direct API call (still available)
        response = await client.get(PerformanceEndpoints.CLIENT_CAMPAIGN)
        print(f"Direct call: {len(response.get('list', []))} campaigns")


async def performance_with_retry_example():
    """Example: Performance API with custom retry and progress callbacks.

    This demonstrates how to handle the unreliable Performance API:
    - Custom retry configuration for 429 errors
    - Progress callbacks for report polling
    """

    # Retry callback - called before each retry attempt
    def on_retry(attempt: int, delay: float, error: Exception) -> None:
        print(f"⚠️  Retry {attempt}: waiting {delay:.1f}s due to: {error}")

    # Progress callback - called on each polling attempt
    def on_progress(progress: ReportPollingProgress) -> None:
        print(f"📊 {progress}")

    # Custom retry config for Performance API (more aggressive)
    retry_config = RetryConfig(
        max_retries=10,        # More retries for flaky API
        base_delay=2.0,        # Start with 2 second delay
        max_delay=120.0,       # Up to 2 minutes between retries
        exponential_base=2.0,  # Double delay each retry
        jitter=True,           # Avoid thundering herd
        on_retry=on_retry,     # Get notified on retries
    )

    async with PerformanceAPIClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
        retry_config=retry_config,
    ) as client:
        print("🚀 Fetching campaigns...")
        campaigns = await client.campaigns.get_campaigns()
        print(f"✅ Found {len(campaigns)} campaigns")

        if campaigns:
            campaign_ids = [str(c["id"]) for c in campaigns[:3]]
            date_from = datetime.now() - timedelta(days=7)
            date_to = datetime.now()

            print(f"\n📈 Requesting statistics report for {len(campaign_ids)} campaigns...")
            report = await client.campaigns.get_statistics_report(
                campaign_ids=campaign_ids,
                date_from=date_from,
                date_to=date_to,
                max_attempts=30,     # Poll up to 30 times
                poll_interval=10.0,  # Every 10 seconds
                on_progress=on_progress,  # Get progress updates
            )
            print(f"\n✅ Report ready! Rows: {len(report.get('rows', []))}")


if __name__ == "__main__":
    # asyncio.run(seller_example())
    # asyncio.run(performance_example())
    # asyncio.run(performance_with_retry_example())
    print("ozon-api-sdk ready")
