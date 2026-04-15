from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import CallbackQuery

from app import texts
from app.config import settings
from app.services import rub_orders
from app.services.buy_access_screen import apply_buy_rub_payment_screen
from app.services.wata_client import create_payment_link

logger = logging.getLogger(__name__)


async def open_buy_rub_payment_after_promo(
    query: CallbackQuery,
    bot: Bot,
    *,
    months: int,
    back_to: str,
) -> str | None:
    """
    После «Пропустить» на промокоде: при WATA — заказ + платёжная ссылка, иначе статический URL или заглушка.

    Возвращает текст для show_alert при ошибке создания ссылки; иначе None (ответ на callback делает вызывающий).
    """
    if not settings.wata_api_configured():
        await apply_buy_rub_payment_screen(
            query, bot, months=months, back_to=back_to, pay_url=None
        )
        return None

    user = query.from_user
    if user is None:
        return None

    tid = user.id
    amount = texts.rub_tariff_amount_rub(months)
    order_id = rub_orders.new_order_id(tid)
    await rub_orders.insert_pending_order(
        order_id=order_id,
        telegram_id=tid,
        months=months,
        amount_rub=amount,
    )

    try:
        link = await create_payment_link(
            amount=float(amount),
            currency="RUB",
            order_id=order_id,
            description=f"VPN {months} мес.",
            link_type="OneTime",
        )
    except Exception:
        logger.exception("WATA: create_payment_link")
        await rub_orders.delete_pending_order(order_id)
        await apply_buy_rub_payment_screen(
            query, bot, months=months, back_to=back_to, pay_url=None
        )
        return texts.WATA_CREATE_LINK_FAILED_ALERT

    pay_url = link.get("url")
    lid = link.get("id")
    if not pay_url or not lid:
        logger.error("WATA: в ответе нет url или id: %s", link)
        await rub_orders.delete_pending_order(order_id)
        await apply_buy_rub_payment_screen(
            query, bot, months=months, back_to=back_to, pay_url=None
        )
        return texts.WATA_CREATE_LINK_FAILED_ALERT

    await rub_orders.save_wata_link_for_order(
        order_id=order_id,
        wata_payment_link_id=str(lid),
        payment_url=str(pay_url),
    )
    await apply_buy_rub_payment_screen(
        query, bot, months=months, back_to=back_to, pay_url=str(pay_url)
    )
    return None
