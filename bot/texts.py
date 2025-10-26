from __future__ import annotations

from .catalog import Product


WELCOME_MESSAGE = (
    "Привет! Я SKLAD_NF бот-магазин. Помогу выбрать корейскую косметику,"
    " оформить заказ и подсказать варианты оплаты."
)

CATALOG_INTRO = (
    "Выберите категорию, чтобы посмотреть доступные позиции."
)

REVIEWS_MESSAGE = (
    "Отзывы 💬 BEAUTY_NF — живой чат клиентов. Присоединяйтесь:"
    " https://t.me/+example_reviews"
)

SUPPORT_MESSAGE = (
    "Напишите нам в поддержку @beauty_support или ответьте на это сообщение,"
    " и менеджер свяжется с вами." 
)

SHIPPING_MESSAGE = (
    "📦 Доставка и оплата\n\n"
    "• СДЭК, Boxberry — отправка на следующий день после оплаты\n"
    "• Почта России — оформляем трек за 10 минут\n"
    "• Самовывоз из пункта SKLAD_NF (Наро-Фоминск)\n\n"
    "Оплата: СБП (без комиссии), YooKassa, CloudPayments."
)


def render_product_card(product: Product) -> str:
    highlights = "\n".join(f"— {item}" for item in product.highlights)
    return (
        f"{product.title}\n"
        f"{highlights}\n"
        f"💰 {product.formatted_price} ₽\n"
        f"📦 Объём: {product.volume}"
    )


def render_cart_summary(items: list[Product]) -> str:
    if not items:
        return "Ваша корзина пуста. Добавьте товары из каталога."

    lines = ["🧺 Корзина"]
    total = 0
    for index, product in enumerate(items, start=1):
        lines.append(f"{index}. {product.title} — {product.formatted_price} ₽")
        total += product.price
    lines.append("")
    lines.append(f"Итого: {total:,} ₽".replace(",", " "))
    lines.append("Нажмите «✅ Оформить заказ», чтобы подтвердить покупку.")
    return "\n".join(lines)


def render_order_summary(order_id: int, total: int, payment_method: str) -> str:
    total_formatted = f"{total:,} ₽".replace(",", " ")
    return (
        f"Заказ №{order_id} создан. К оплате {total_formatted}.\n"
        f"Способ оплаты: {payment_method}."
    )


def payment_instructions(method: str) -> str:
    instructions = {
        "СБП": (
            "Оплатите по персональной ссылке СБП: https://www.sbp.example/link\n"
            "После оплаты отправьте чек или скрин, чтобы мы подтвердили заказ."
        ),
        "YooKassa": (
            "Ссылка на оплату через YooKassa придёт отдельным сообщением."
            " Оплата фиксирует заказ автоматически."
        ),
        "CloudPayments": (
            "Введите данные карты на защищённой странице CloudPayments."
            " Статус заказа обновится сразу после платежа."
        ),
    }
    return instructions.get(
        method,
        "Менеджер свяжется с вами для подтверждения способа оплаты.",
    )
