from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class CatalogCallback(CallbackData, prefix="catalog"):
    """Callback schema for catalog navigation."""

    level: int
    category: str | None = None
    product_id: str | None = None
    action: str | None = None


class CartCallback(CallbackData, prefix="cart"):
    action: str
