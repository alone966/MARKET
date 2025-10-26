from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CheckoutState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()
    waiting_for_comment = State()
    waiting_for_payment_method = State()
