from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from .callbacks import CartCallback, CatalogCallback
from .catalog import Category, Product, get_catalog


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💄 Каталог"),
        KeyboardButton(text="🛍 Мои заказы"),
    )
    builder.row(
        KeyboardButton(text="💬 Отзывы"),
        KeyboardButton(text="📦 Доставка и оплата"),
    )
    builder.row(KeyboardButton(text="✉️ Поддержка"))
    return builder.as_markup(resize_keyboard=True)


def catalog_categories_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in get_catalog():
        builder.button(
            text=category.title,
            callback_data=CatalogCallback(level=1, category=category.slug).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


def category_products_keyboard(category: Category) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in category.products:
        builder.button(
            text=product.title,
            callback_data=CatalogCallback(
                level=2,
                category=category.slug,
                product_id=product.id,
                action="open",
            ).pack(),
        )
    builder.button(
        text="⬅️ Назад к категориям",
        callback_data=CatalogCallback(level=0).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def product_actions_keyboard(category: Category, product: Product) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛒 Добавить в корзину",
        callback_data=CatalogCallback(
            level=2, category=category.slug, product_id=product.id, action="add"
        ).pack(),
    )
    builder.button(
        text="⚡️ Купить сейчас",
        callback_data=CatalogCallback(
            level=2, category=category.slug, product_id=product.id, action="buy"
        ).pack(),
    )
    builder.button(
        text="⬅️ Назад",
        callback_data=CatalogCallback(level=1, category=category.slug).pack(),
    )
    builder.button(
        text="🧺 Корзина",
        callback_data=CartCallback(action="view").pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def cart_management_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Оформить заказ",
        callback_data=CartCallback(action="checkout").pack(),
    )
    builder.button(
        text="🧹 Очистить корзину",
        callback_data=CartCallback(action="clear").pack(),
    )
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="СБП"),
        KeyboardButton(text="YooKassa"),
    )
    builder.row(KeyboardButton(text="CloudPayments"))
    builder.row(KeyboardButton(text="⬅️ Отмена"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def delivery_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="СДЭК"),
        KeyboardButton(text="Boxberry"),
    )
    builder.row(
        KeyboardButton(text="Почта России"),
        KeyboardButton(text="Самовывоз SKLAD_NF"),
    )
    builder.row(KeyboardButton(text="⬅️ Отмена"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
