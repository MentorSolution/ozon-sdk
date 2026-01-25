"""Common type aliases for Ozon API SDK."""

from typing import Any, TypedDict

# Generic API response types
APIItem = dict[str, Any]
APIItemsList = list[APIItem]
APIResult = dict[str, Any]


class ActivateProduct(TypedDict):
    """Product data for activation in a promotion."""

    product_id: int
    action_price: float
    stock: int
