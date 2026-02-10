import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from ozon_api_sdk import SellerAPIClient, PerformanceAPIClient

load_dotenv()

RESPONSES_DIR = Path(__file__).parent / "responses"


def pytest_addoption(parser):
    parser.addoption(
        "--save-responses",
        action="store_true",
        default=False,
        help="Save API responses to tests/responses/ as JSON files.",
    )
    parser.addoption(
        "--clean-responses",
        action="store_true",
        default=False,
        help="Remove all saved responses from tests/responses/ and exit.",
    )


def pytest_sessionstart(session):
    if session.config.getoption("--clean-responses"):
        import shutil

        if RESPONSES_DIR.exists():
            shutil.rmtree(RESPONSES_DIR)
        session.config._clean_responses_done = True


def pytest_collection_modifyitems(config, items):
    if getattr(config, "_clean_responses_done", False):
        items.clear()


@pytest.fixture
def save_response(request):
    """Fixture that returns a function to save API response to JSON.

    Keeps two versions per test for comparison:
        {test_name}.prev.json  — previous run
        {test_name}.latest.json — current run

    On each run, latest is moved to prev, and new data is saved as latest.
    Only saves when --save-responses flag is passed.
    """
    def _save(data):
        if not request.config.getoption("--save-responses"):
            return
        RESPONSES_DIR.mkdir(exist_ok=True)
        name = request.node.name
        latest = RESPONSES_DIR / f"{name}.latest.json"
        prev = RESPONSES_DIR / f"{name}.prev.json"

        if latest.exists():
            prev.write_bytes(latest.read_bytes())

        with open(latest, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    return _save


@pytest.fixture
async def seller_client():
    client_id = os.environ.get("OZON_SELLER_CLIENT_ID")
    api_key = os.environ.get("OZON_SELLER_API_KEY")

    if not client_id or not api_key:
        pytest.skip(
            "OZON_SELLER_CLIENT_ID and OZON_SELLER_API_KEY not set. "
            "Add them to .env file in the project root or export as env variables."
        )

    async with SellerAPIClient(client_id=client_id, api_key=api_key) as client:
        yield client


@pytest.fixture
async def performance_client():
    client_id = os.environ.get("OZON_PERF_CLIENT_ID")
    client_secret = os.environ.get("OZON_PERF_CLIENT_SECRET")

    if not client_id or not client_secret:
        pytest.skip(
            "OZON_PERF_CLIENT_ID and OZON_PERF_CLIENT_SECRET not set. "
            "Add them to .env file in the project root or export as env variables."
        )

    async with PerformanceAPIClient(
        client_id=client_id, client_secret=client_secret
    ) as client:
        yield client
