from __future__ import annotations

from aiogram import Bot
from aiogram.types import CallbackQuery

from app import texts
from app.services import rub_orders
from app.services.buy_access_screen import apply_buy_stars_payment_screen


def stars_invoice_payload(order_id: str) -> str:
    return f"stars:{order_id}"


def parse_stars_invoice_payload(payload: str | None) -> str | None:
    raw = str(payload or "").strip()
    if not raw.startswith("stars:"):
        return None
    order_id = raw.split(":", 1)[1].strip()
    return order_id or None


async def open_buy_stars_payment_screen(
    query: CallbackQuery,
    bot: Bot,
    *,
    months: int,
    back_to: str,
) -> str:
    user = query.from_user
    if user is None:
        raise RuntimeError("Не удалось определить пользователя")

    amount = texts.stars_tariff_amount(months)
    order_id = rub_orders.new_order_id(user.id)
    await rub_orders.insert_pending_order(
        order_id=order_id,
        telegram_id=user.id,
        months=months,
        amount_rub=amount,
        payment_method="stars",
        currency="XTR",
    )
    await apply_buy_stars_payment_screen(
        query,
        bot,
        order_id=order_id,
        months=months,
        back_to=back_to,
    )
    return order_id
