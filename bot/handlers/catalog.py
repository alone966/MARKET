from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..callbacks import CartCallback, CatalogCallback
from ..cart import add_to_cart, clear_cart, get_cart, replace_cart_with_single
from ..catalog import Category, Product, find_category, find_product
from ..database import OrderStorage
from ..config import settings
from ..keyboards import (
    cart_management_keyboard,
    catalog_categories_keyboard,
    category_products_keyboard,
    delivery_keyboard,
    main_menu,
    payment_keyboard,
    product_actions_keyboard,
)
from ..states import CheckoutState
from ..texts import (
    CATALOG_INTRO,
    payment_instructions,
    render_cart_summary,
    render_order_summary,
    render_product_card,
)

router = Router()

order_storage = OrderStorage(settings.database_path)


async def _get_category(slug: str | None) -> Category | None:
    if not slug:
        return None
    return find_category(slug)


async def _get_product(product_id: str | None) -> Product | None:
    if not product_id:
        return None
    return find_product(product_id)


async def _start_checkout(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Давайте оформим заказ. Укажите, пожалуйста, ваше имя и фамилию.",
    )
    await state.set_state(CheckoutState.waiting_for_name)


@router.callback_query(CatalogCallback.filter(F.level == 0))
async def show_categories(callback: CallbackQuery) -> None:
    await callback.message.edit_text(CATALOG_INTRO, reply_markup=catalog_categories_keyboard())
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.level == 1))
async def show_products(callback: CallbackQuery, callback_data: CatalogCallback) -> None:
    category = await _get_category(callback_data.category)
    if not category:
        await callback.answer("Категория недоступна", show_alert=True)
        return
    await callback.message.edit_text(
        f"{category.title}. Выберите товар:",
        reply_markup=category_products_keyboard(category),
    )
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.level == 2, F.action == "open"))
async def product_details(callback: CallbackQuery, callback_data: CatalogCallback) -> None:
    category = await _get_category(callback_data.category)
    product = await _get_product(callback_data.product_id)
    if not category or not product:
        await callback.answer("Товар недоступен", show_alert=True)
        return
    text = render_product_card(product)
    await callback.message.answer_photo(
        photo=product.image_url,
        caption=text,
        reply_markup=product_actions_keyboard(category, product),
    )
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.level == 2, F.action == "add"))
async def add_product_to_cart(
    callback: CallbackQuery, callback_data: CatalogCallback, state: FSMContext
) -> None:
    product = await _get_product(callback_data.product_id)
    if not product:
        await callback.answer("Не удалось добавить товар", show_alert=True)
        return
    await add_to_cart(state, product.id)
    await callback.answer("Добавлено в корзину")


@router.callback_query(CatalogCallback.filter(F.level == 2, F.action == "buy"))
async def buy_now(
    callback: CallbackQuery, callback_data: CatalogCallback, state: FSMContext
) -> None:
    product = await _get_product(callback_data.product_id)
    if not product:
        await callback.answer("Товар недоступен", show_alert=True)
        return
    await replace_cart_with_single(state, product.id)
    await callback.answer()
    await _start_checkout(callback.message, state)


@router.callback_query(CartCallback.filter(F.action == "view"))
async def show_cart(callback: CallbackQuery, state: FSMContext) -> None:
    items = await get_cart(state)
    summary = render_cart_summary(items)
    reply_markup = cart_management_keyboard() if items else None
    await callback.message.answer(summary, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(CartCallback.filter(F.action == "clear"))
async def clear_user_cart(callback: CallbackQuery, state: FSMContext) -> None:
    await clear_cart(state)
    await callback.message.answer("Корзина очищена.")
    await callback.answer()


@router.callback_query(CartCallback.filter(F.action == "checkout"))
async def checkout_from_cart(callback: CallbackQuery, state: FSMContext) -> None:
    items = await get_cart(state)
    if not items:
        await callback.answer("Сначала добавьте товары", show_alert=True)
        return
    await callback.answer()
    await _start_checkout(callback.message, state)


@router.message(F.text == "🛍 Мои заказы")
async def show_orders(message: Message, state: FSMContext) -> None:
    items = await get_cart(state)
    summary = render_cart_summary(items)
    await message.answer(summary, reply_markup=cart_management_keyboard() if items else None)

    orders = list(order_storage.list_orders(message.from_user.id))
    if not orders:
        await message.answer("У вас ещё нет оформленных заказов. После оплаты статус появится здесь.")
        return

    for order in orders[:5]:
        total_formatted = f"{order.total_price:,} ₽".replace(",", " ")
        text = (
            f"Заказ №{order.id} от {order.created_at:%d.%m.%Y}\n"
            f"Сумма: {total_formatted}\n"
            f"Статус: {order.status}\n"
            f"Способ оплаты: {order.payment_method}"
        )
        await message.answer(text)


async def _persist_order(
    message: Message,
    items: list[Product],
    payment_method: str,
    customer_name: str,
    customer_phone: str,
    delivery_address: str,
    comment: str | None,
) -> tuple[int, int]:
    payload = [
        {
            "id": product.id,
            "title": product.title,
            "price": product.price,
        }
        for product in items
    ]
    total_price = sum(product.price for product in items)
    order_id = order_storage.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        items=payload,
        total_price=total_price,
        payment_method=payment_method,
        status="ожидает оплаты",
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address,
        comment=comment,
    )
    return order_id, total_price


async def _notify_admin(message: Message, order_id: int, payment_method: str) -> None:
    if not settings.admin_chat_id:
        return
    await message.bot.send_message(
        chat_id=settings.admin_chat_id,
        text=(
            f"Новый заказ №{order_id}\n"
            f"Покупатель: @{message.from_user.username or '—'} (ID {message.from_user.id})\n"
            f"Оплата: {payment_method}"
        ),
    )


@router.message(CheckoutState.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=message.text.strip())
    await message.answer("Оставьте номер телефона для связи (в формате +7...).")
    await state.set_state(CheckoutState.waiting_for_phone)


@router.message(CheckoutState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_phone=message.text.strip())
    await message.answer(
        "Выберите способ доставки:",
        reply_markup=delivery_keyboard(),
    )
    await state.set_state(CheckoutState.waiting_for_delivery)


@router.message(CheckoutState.waiting_for_delivery, F.text == "⬅️ Отмена")
@router.message(CheckoutState.waiting_for_comment, F.text == "⬅️ Отмена")
@router.message(CheckoutState.waiting_for_payment_method, F.text == "⬅️ Отмена")
async def cancel_checkout(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Оформление заказа отменено.", reply_markup=main_menu())


@router.message(CheckoutState.waiting_for_delivery)
async def process_delivery(message: Message, state: FSMContext) -> None:
    await state.update_data(delivery_address=message.text.strip())
    await message.answer(
        "Оставьте комментарий для менеджера (или напишите «Без комментариев»).",
    )
    await state.set_state(CheckoutState.waiting_for_comment)


@router.message(CheckoutState.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    comment = message.text.strip()
    await state.update_data(comment=None if comment.lower() == "без комментариев" else comment)
    await message.answer(
        "Выберите способ оплаты:",
        reply_markup=payment_keyboard(),
    )
    await state.set_state(CheckoutState.waiting_for_payment_method)


@router.message(CheckoutState.waiting_for_payment_method)
async def process_payment_method(message: Message, state: FSMContext) -> None:
    payment_method = message.text.strip()
    if payment_method not in {"СБП", "YooKassa", "CloudPayments"}:
        await message.answer("Выберите вариант из списка.")
        return

    data = await state.get_data()
    items = await get_cart(state)
    order_id, total_price = await _persist_order(
        message=message,
        items=items,
        payment_method=payment_method,
        customer_name=data.get("customer_name", ""),
        customer_phone=data.get("customer_phone", ""),
        delivery_address=data.get("delivery_address", ""),
        comment=data.get("comment"),
    )

    await message.answer(
        render_order_summary(order_id, total_price, payment_method)
    )
    await message.answer(payment_instructions(payment_method))
    await _notify_admin(message, order_id, payment_method)
    await clear_cart(state)
    await state.clear()
    await message.answer(
        "Если хотите продолжить покупки — откройте каталог.", reply_markup=main_menu()
    )
