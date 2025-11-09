"""Excel export helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional

import pandas as pd

from .models import Product

GREEN = "background-color: #d4edda"
RED = "background-color: #f8d7da"
YELLOW = "background-color: #fff3cd"
BLUE = "background-color: #cfe2ff"


def _build_dataframe(products: Iterable[Product], store_city: str) -> pd.DataFrame:
    records: List[dict] = []
    for product in products:
        stock_city = product.stock_by_city.get(store_city)
        total_stock = None
        if product.stock_by_city:
            numbers = [value for value in product.stock_by_city.values() if isinstance(value, int)]
            total_stock = sum(numbers) if numbers else None
        records.append(
            {
                "Категория": product.category,
                "Артикул": product.sku,
                "Наименование": product.name,
                "Описание": product.description,
                "Цена": product.price,
                "Валюта": product.currency,
                f"Остаток ({store_city})": stock_city,
                "Всего на складах": total_stock,
                "Ссылка": product.url,
            }
        )
    df = pd.DataFrame(records)
    return df


def _build_summary(diff: dict, store_city: str) -> pd.DataFrame:
    rows: List[dict] = []
    for sku, record in diff.get("new", {}).items():
        rows.append(
            {
                "Тип": "Новый товар",
                "Артикул": sku,
                "Наименование": record.get("name"),
                f"Остаток ({store_city})": (record.get("stock_by_city") or {}).get(store_city),
            }
        )
    for sku, record in diff.get("removed", {}).items():
        rows.append(
            {
                "Тип": "Удален",
                "Артикул": sku,
                "Наименование": record.get("name"),
                f"Остаток ({store_city})": (record.get("stock_by_city") or {}).get(store_city),
            }
        )
    for sku, payload in diff.get("changed", {}).items():
        rows.append(
            {
                "Тип": "Изменения",
                "Артикул": sku,
                "Наименование": payload.get("record", {}).get("name"),
                "Изменения": ", ".join(sorted(payload.get("changes", {}).keys())),
                f"Остаток ({store_city})": (payload.get("record", {}).get("stock_by_city") or {}).get(store_city),
            }
        )
    return pd.DataFrame(rows)


def _highlight_changes(diff: dict, store_city: str):
    new = diff.get("new", {})
    removed = diff.get("removed", {})
    changed = diff.get("changed", {})

    def formatter(row: pd.Series) -> List[str]:
        sku = row["Артикул"]
        styles = ["" for _ in row]
        columns = list(row.index)
        if sku in new:
            return [GREEN for _ in row]
        if sku in removed:
            return [RED for _ in row]
        if sku in changed:
            change_info = changed[sku]["changes"]
            for idx, column in enumerate(columns):
                key = _column_to_snapshot_key(column, store_city)
                if key is None:
                    continue
                if key == "stock_by_city":
                    old = (change_info.get("stock_by_city", {}).get("old") or {}).get(store_city)
                    new_value = (change_info.get("stock_by_city", {}).get("new") or {}).get(store_city)
                    if old != new_value:
                        styles[idx] = YELLOW
                elif key in change_info:
                    styles[idx] = BLUE if key == "price" else YELLOW
        return styles

    return formatter


def _column_to_snapshot_key(column: str, store_city: str) -> Optional[str]:
    if column == "Категория":
        return "category"
    if column == "Наименование":
        return "name"
    if column == "Описание":
        return "description"
    if column == "Цена":
        return "price"
    if column == f"Остаток ({store_city})":
        return "stock_by_city"
    if column == "Всего на складах":
        return "stock_by_city"
    return None


def export_to_excel(
    products: Iterable[Product],
    diff: dict,
    output_path: str,
    generated_at: datetime,
    store_city: str,
) -> None:
    df = _build_dataframe(products, store_city)
    formatter = _highlight_changes(diff, store_city)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        styled = df.style.apply(formatter, axis=1)
        styled.format({"Цена": "{:,.2f}"})
        styled.to_excel(writer, sheet_name="Каталог", index=False)

        summary_df = _build_summary(diff, store_city)
        summary_df.to_excel(writer, sheet_name="Изменения", index=False)

        meta_df = pd.DataFrame(
            {
                "Параметр": ["Дата выгрузки", "Количество товаров"],
                "Значение": [generated_at.strftime("%Y-%m-%d %H:%M"), len(df)],
            }
        )
        meta_df.to_excel(writer, sheet_name="Сводка", index=False)


__all__ = ["export_to_excel"]
