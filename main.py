import asyncio

from ozon_api_sdk import SellerAPIClient, PerformanceAPIClient


async def seller_example():
    """Example: Seller API usage."""
    async with SellerAPIClient(
        client_id=123456,
        api_key="your-api-key",
    ) as client:
        # Get product list
        response = await client.post("/v2/product/list", {
            "filter": {},
            "limit": 100,
        })
        print(response)


async def performance_example():
    """Example: Performance API usage."""
    async with PerformanceAPIClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
    ) as client:
        # Get campaigns
        response = await client.get("/api/client/campaign")
        print(response)


if __name__ == "__main__":
    # asyncio.run(seller_example())
    # asyncio.run(performance_example())
    print("ozon-api-sdk ready")
