"""Snapshot storage utilities for inventory comparisons."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

from .models import Product

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass(slots=True)
class Snapshot:
    generated_at: datetime
    products: Dict[str, dict]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.strftime(ISO_FORMAT),
            "products": self.products,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Snapshot":
        timestamp = datetime.strptime(payload["generated_at"], ISO_FORMAT)
        products = payload.get("products", {})
        return cls(generated_at=timestamp, products=products)


def product_to_record(product: Product) -> dict:
    return {
        "sku": product.sku,
        "category": product.category,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "stock_by_city": product.stock_by_city,
        "url": product.url,
    }


def build_snapshot(products: Iterable[Product], generated_at: Optional[datetime] = None) -> Snapshot:
    timestamp = generated_at or datetime.now()
    data = {product.sku: product_to_record(product) for product in products}
    return Snapshot(generated_at=timestamp, products=data)


def load_snapshot(path: Path) -> Optional[Snapshot]:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return Snapshot.from_dict(payload)


def save_snapshot(path: Path, snapshot: Snapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def diff_snapshots(current: Snapshot, previous: Optional[Snapshot]) -> dict:
    previous_products = previous.products if previous else {}
    current_products = current.products

    new_skus = sorted(set(current_products) - set(previous_products))
    removed_skus = sorted(set(previous_products) - set(current_products))
    common_skus = set(current_products) & set(previous_products)

    changed: Dict[str, Dict[str, dict]] = {}

    for sku in common_skus:
        current_record = current_products[sku]
        previous_record = previous_products[sku]
        changes = {}
        for key in ("price", "stock_by_city", "name", "description", "category"):
            if current_record.get(key) != previous_record.get(key):
                changes[key] = {
                    "old": previous_record.get(key),
                    "new": current_record.get(key),
                }
        if changes:
            changed[sku] = {
                "changes": changes,
                "record": current_record,
            }

    return {
        "new": {sku: current_products[sku] for sku in new_skus},
        "removed": {sku: previous_products[sku] for sku in removed_skus},
        "changed": changed,
    }


__all__ = [
    "Snapshot",
    "build_snapshot",
    "load_snapshot",
    "save_snapshot",
    "diff_snapshots",
]
