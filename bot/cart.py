from __future__ import annotations

from typing import List

from aiogram.fsm.context import FSMContext

from .catalog import Product, find_product


async def get_cart(state: FSMContext) -> List[Product]:
    data = await state.get_data()
    product_ids: list[str] = data.get("cart", [])
    items: list[Product] = []
    for product_id in product_ids:
        product = find_product(product_id)
        if product:
            items.append(product)
    return items


async def add_to_cart(state: FSMContext, product_id: str) -> None:
    data = await state.get_data()
    product_ids: list[str] = data.get("cart", [])
    product_ids.append(product_id)
    await state.update_data(cart=product_ids)


async def clear_cart(state: FSMContext) -> None:
    await state.update_data(cart=[])


async def replace_cart_with_single(state: FSMContext, product_id: str) -> None:
    await state.update_data(cart=[product_id])
