"""Ozon API parameter constants.

Usage:
    from ozon_api_sdk.constants import ProductVisibility, CampaignState

    await client.products.get_products_by_visibility(ProductVisibility.ARCHIVED)
    campaigns = await client.campaigns.get_campaigns(states=[CampaignState.RUNNING])
"""

from typing import Literal


class ProductVisibility:
    """Product visibility filter values for /v2/product/list."""

    ALL = "ALL"
    VISIBLE = "VISIBLE"
    INVISIBLE = "INVISIBLE"
    EMPTY_STOCK = "EMPTY_STOCK"
    NOT_MODERATED = "NOT_MODERATED"
    MODERATED = "MODERATED"
    DISABLED = "DISABLED"
    STATE_FAILED = "STATE_FAILED"
    READY_TO_SUPPLY = "READY_TO_SUPPLY"
    VALIDATION_STATE_PENDING = "VALIDATION_STATE_PENDING"
    VALIDATION_STATE_FAIL = "VALIDATION_STATE_FAIL"
    VALIDATION_STATE_SUCCESS = "VALIDATION_STATE_SUCCESS"
    TO_SUPPLY = "TO_SUPPLY"
    IN_SALE = "IN_SALE"
    REMOVED_FROM_SALE = "REMOVED_FROM_SALE"
    BANNED = "BANNED"
    OVERPRICED = "OVERPRICED"
    CRITICALLY_OVERPRICED = "CRITICALLY_OVERPRICED"
    EMPTY_BARCODE = "EMPTY_BARCODE"
    BARCODE_EXISTS = "BARCODE_EXISTS"
    QUARANTINE = "QUARANTINE"
    ARCHIVED = "ARCHIVED"
    OVERPRICED_WITH_STOCK = "OVERPRICED_WITH_STOCK"
    PARTIAL_APPROVED = "PARTIAL_APPROVED"
    IMAGE_ABSENT = "IMAGE_ABSENT"
    MODERATION_BLOCK = "MODERATION_BLOCK"


Dimension = Literal[
    "sku",
    "spu",
    "day",
    "week",
    "month"
]

Metrics = Literal[
    "revenue",
    "ordered_units"
]

class CampaignState:
    """Campaign state values for Performance API campaigns."""

    UNKNOWN = "CAMPAIGN_STATE_UNKNOWN"
    RUNNING = "CAMPAIGN_STATE_RUNNING"
    PLANNED = "CAMPAIGN_STATE_PLANNED"
    STOPPED = "CAMPAIGN_STATE_STOPPED"
    INACTIVE = "CAMPAIGN_STATE_INACTIVE"
    ARCHIVED = "CAMPAIGN_STATE_ARCHIVED"
    MODERATION_DRAFT = "CAMPAIGN_STATE_MODERATION_DRAFT"
    MODERATION_IN_PROGRESS = "CAMPAIGN_STATE_MODERATION_IN_PROGRESS"
    MODERATION_FAILED = "CAMPAIGN_STATE_MODERATION_FAILED"
    FINISHED = "CAMPAIGN_STATE_FINISHED"


class AdvertisingType:
    """Advertising object types for Performance API campaigns."""

    SKU = "SKU"
    SEARCH_PROMO = "SEARCH_PROMO"
    BANNER = "BANNER"
    BRAND_SHELF = "BRAND_SHELF"
    VIDEO = "VIDEO"


class PaymentType:
    """Payment types for Performance API campaigns."""

    CPC = "CPC"  # Cost Per Click
    CPM = "CPM"  # Cost Per Mille (1000 impressions)
    CPO = "CPO"  # Cost Per Order


class StatisticsGroupBy:
    """Group by options for Performance API statistics reports."""

    DATE = "DATE"
    NO_GROUP_BY = "NO_GROUP_BY"
    START_OF_WEEK = "START_OF_WEEK"
    START_OF_MONTH = "START_OF_MONTH"
