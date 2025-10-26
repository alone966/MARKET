from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .. import texts
from ..keyboards import catalog_categories_keyboard, main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.WELCOME_MESSAGE, reply_markup=main_menu())
    await message.answer(texts.CATALOG_INTRO, reply_markup=catalog_categories_keyboard())


@router.message(F.text == "💄 Каталог")
async def show_catalog(message: Message) -> None:
    await message.answer(texts.CATALOG_INTRO, reply_markup=catalog_categories_keyboard())


@router.message(F.text == "💬 Отзывы")
async def show_reviews(message: Message) -> None:
    await message.answer(texts.REVIEWS_MESSAGE)


@router.message(F.text == "📦 Доставка и оплата")
async def show_shipping(message: Message) -> None:
    await message.answer(texts.SHIPPING_MESSAGE)


@router.message(F.text == "✉️ Поддержка")
async def support(message: Message) -> None:
    await message.answer(texts.SUPPORT_MESSAGE)
