from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class Order:
    id: int
    user_id: int
    username: str | None
    items: list[dict]
    total_price: int
    payment_method: str
    status: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    comment: str | None
    created_at: datetime


class OrderStorage:
    """Tiny SQLite wrapper for persisting orders."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self._path)
        try:
            yield connection
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    items TEXT NOT NULL,
                    total_price INTEGER NOT NULL,
                    payment_method TEXT NOT NULL,
                    status TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    delivery_address TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_order(
        self,
        *,
        user_id: int,
        username: str | None,
        items: list[dict],
        total_price: int,
        payment_method: str,
        status: str,
        customer_name: str,
        customer_phone: str,
        delivery_address: str,
        comment: str | None,
    ) -> int:
        payload = json.dumps(items, ensure_ascii=False)
        created_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO orders (
                    user_id, username, items, total_price, payment_method,
                    status, customer_name, customer_phone, delivery_address, comment, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    payload,
                    total_price,
                    payment_method,
                    status,
                    customer_name,
                    customer_phone,
                    delivery_address,
                    comment,
                    created_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_orders(self, user_id: int) -> Iterable[Order]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            )
            for row in cursor.fetchall():
                yield self._deserialize_order(row)

    def _deserialize_order(self, row: tuple) -> Order:
        (
            order_id,
            user_id,
            username,
            items_json,
            total_price,
            payment_method,
            status,
            customer_name,
            customer_phone,
            delivery_address,
            comment,
            created_at,
        ) = row
        items = json.loads(items_json)
        return Order(
            id=int(order_id),
            user_id=int(user_id),
            username=username,
            items=items,
            total_price=int(total_price),
            payment_method=payment_method,
            status=status,
            customer_name=customer_name,
            customer_phone=customer_phone,
            delivery_address=delivery_address,
            comment=comment,
            created_at=datetime.fromisoformat(created_at),
        )
