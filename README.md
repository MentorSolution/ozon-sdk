# ozon-api-sdk

Async Python SDK for Ozon APIs (Seller API and Performance API).

## Features

- Async/await support with `httpx`
- Automatic retry with exponential backoff on 429/5xx errors
- Rate limiting via semaphore
- OAuth2 token auto-refresh for Performance API
- Progress callbacks for long-running report generation
- Type hints throughout

## Installation

```bash
pip install ozon-api-sdk @ git+https://github.com/MentorSolution/ozon-sdk.git
```

Or add to `pyproject.toml`:
```toml
dependencies = [
    "ozon-api-sdk @ git+https://github.com/MentorSolution/ozon-sdk.git",
]
```

## Requirements

- Python 3.13+
- httpx

## Quick Start

### Seller API

```python
import asyncio
from datetime import datetime, timedelta
from ozon_api_sdk import SellerAPIClient

async def main():
    async with SellerAPIClient(
        client_id=123456,
        api_key="your-api-key",
    ) as client:
        # Get products
        products = await client.products.get_products()
        print(f"Found {len(products)} products")

        # Get product info
        offer_ids = [p["offer_id"] for p in products[:10]]
        info = await client.products.get_product_info(offer_ids)

        # Get transactions
        transactions = await client.finance.get_transactions(
            date_from=datetime.now() - timedelta(days=30),
            date_to=datetime.now(),
        )

asyncio.run(main())
```

### Performance API

```python
import asyncio
from datetime import datetime, timedelta
from ozon_api_sdk import PerformanceAPIClient

async def main():
    async with PerformanceAPIClient(
        client_id="your-client-id",
        client_secret="your-client-secret",
    ) as client:
        # Get campaigns
        campaigns = await client.campaigns.get_campaigns()
        print(f"Found {len(campaigns)} campaigns")

        # Get statistics report
        if campaigns:
            campaign_ids = [str(c["id"]) for c in campaigns[:5]]
            report = await client.campaigns.get_statistics_report(
                campaign_ids=campaign_ids,
                date_from=datetime.now() - timedelta(days=7),
                date_to=datetime.now(),
            )

asyncio.run(main())
```

## Advanced Usage

### Custom Retry Configuration

Performance API can be unreliable. Configure retry behavior for your needs:

```python
from ozon_api_sdk import PerformanceAPIClient, RetryConfig

def on_retry(attempt: int, delay: float, error: Exception):
    print(f"Retry {attempt}: waiting {delay:.1f}s - {error}")

retry_config = RetryConfig(
    max_retries=10,        # max retry attempts (default: 5)
    base_delay=2.0,        # initial delay in seconds (default: 1.0)
    max_delay=120.0,       # max delay between retries (default: 60.0)
    exponential_base=2.0,  # backoff multiplier (default: 2.0)
    jitter=True,           # randomize delays (default: True)
    on_retry=on_retry,     # callback before each retry
)

async with PerformanceAPIClient(
    client_id="...",
    client_secret="...",
    retry_config=retry_config,
) as client:
    ...
```

### Report Polling Progress

Track progress of long-running report generation:

```python
from ozon_api_sdk import PerformanceAPIClient, ReportPollingProgress

def on_progress(progress: ReportPollingProgress):
    print(
        f"Report {progress.report_uuid}: "
        f"{progress.progress_percent:.0f}% "
        f"(attempt {progress.attempt}/{progress.max_attempts}, "
        f"status: {progress.status})"
    )

async with PerformanceAPIClient(...) as client:
    report = await client.campaigns.get_statistics_report(
        campaign_ids=["123", "456"],
        date_from=date_from,
        date_to=date_to,
        max_attempts=30,      # poll up to 30 times (default: 30)
        poll_interval=10.0,   # seconds between polls (default: 10.0)
        on_progress=on_progress,
    )
```

### Direct API Calls

Use endpoints directly when subclient methods don't cover your use case:

```python
from ozon_api_sdk import SellerAPIClient, SellerEndpoints

async with SellerAPIClient(...) as client:
    # POST request
    response = await client.post(
        SellerEndpoints.PRODUCT_LIST,
        {"filter": {}, "limit": 100},
    )

    # GET request
    response = await client.get("/v1/some/endpoint", params={"key": "value"})
```

## API Reference

### SellerAPIClient

| Subclient | Method | Description |
|-----------|--------|-------------|
| `products` | `get_products()` | List all products with pagination |
| `products` | `get_product_info(offer_ids)` | Get product details by offer IDs |
| `products` | `get_product_csv_report()` | Request CSV product report |
| `finance` | `get_transactions(date_from, date_to)` | Get financial transactions |
| `finance` | `get_transaction_totals(date_from, date_to)` | Get transaction totals |

### PerformanceAPIClient

| Subclient | Method | Description |
|-----------|--------|-------------|
| `campaigns` | `get_campaigns()` | List advertising campaigns |
| `campaigns` | `get_campaign_by_id(campaign_id)` | Get single campaign |
| `campaigns` | `get_statistics_report(...)` | Generate and fetch statistics report |

## Exceptions

```python
from ozon_api_sdk import OzonAPIError, OzonAuthError, OzonRateLimitError

try:
    products = await client.products.get_products()
except OzonAuthError as e:
    print(f"Auth failed: {e}")  # 401, 403
except OzonRateLimitError as e:
    print(f"Rate limited: {e}")  # 429 (after retries exhausted)
except OzonAPIError as e:
    print(f"API error: {e}")  # Other 4xx/5xx
```

## Documentation

- [Ozon Seller API](https://docs.ozon.ru/api/seller/)
- [Ozon Performance API](https://docs.ozon.ru/api/performance/)

## License

MIT
