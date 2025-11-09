"""Shared data models for the scraper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass(slots=True)
class Product:
    """Representation of a product scraped from Makmart."""

    category: str
    url: str
    sku: str
    name: str
    description: str
    price: Optional[float]
    currency: Optional[str]
    stock_by_city: Dict[str, Optional[int]]
    last_updated: datetime

    @property
    def stock_naro_fominsk(self) -> Optional[int]:
        return self.stock_by_city.get("Наро-Фоминск")


@dataclass(slots=True)
class Category:
    """Representation of a product category."""

    name: str
    url: str


@dataclass(slots=True)
class ScrapeSummary:
    """Summary of the scrape run."""

    generated_at: datetime
    total_products: int
    total_categories: int
    new_products: int
    removed_products: int
    changed_products: int


__all__ = ["Product", "Category", "ScrapeSummary"]
