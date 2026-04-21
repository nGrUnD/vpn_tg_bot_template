from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import CallbackQuery

from app import texts
from app.config import settings
from app.services import rub_orders
from app.services.buy_access_screen import apply_buy_crypto_payment_screen
from app.services.cryptopay_client import create_invoice, invoice_payment_url
from app.services.usdt_rub_rate import get_rub_per_usdt

logger = logging.getLogger(__name__)


async def open_crypto_payment_for_tariff(
    query: CallbackQuery,
    bot: Bot,
    *,
    months: int,
    back_to: str,
) -> str | None:
    """
    Создаёт заказ и инвойс Crypto Pay. При успехе показывает экран с кнопкой-ссылкой.
    Возвращает текст для show_alert при ошибке, иначе None.
    """
    if not settings.cryptopay_api_configured():
        return texts.CRYPTOPAY_NOT_CONFIGURED_ALERT

    user = query.from_user
    if user is None:
        return None

    tid = user.id
    rub_per_usdt = await get_rub_per_usdt()
    amount_dec = texts.crypto_tariff_amount_usdt(months, rub_per_usdt=rub_per_usdt)
    amount_str = texts.format_crypto_usdt(amount_dec)
    order_id = rub_orders.new_order_id(tid)
    desc = texts.cryptopay_invoice_description(months=months, telegram_id=tid)

    await rub_orders.insert_pending_order(
        order_id=order_id,
        telegram_id=tid,
        months=months,
        amount=amount_dec,
        payment_method="crypto",
        currency="USDT",
    )

    try:
        inv = await create_invoice(
            amount_usdt=amount_str,
            description=desc,
            payload=order_id,
        )
    except Exception:
        logger.exception("Crypto Pay: create_invoice")
        await rub_orders.delete_pending_order(order_id)
        await apply_buy_crypto_payment_screen(
            query,
            bot,
            months=months,
            back_to=back_to,
            amount_usdt=amount_dec,
            rub_per_usdt=rub_per_usdt,
            pay_url=None,
        )
        return texts.CRYPTOPAY_CREATE_FAILED_ALERT

    pay_url = invoice_payment_url(inv)
    ext_id = inv.get("invoice_id")
    ext_s = str(ext_id) if ext_id is not None else ""

    if pay_url:
        await rub_orders.save_wata_link_for_order(
            order_id=order_id,
            wata_payment_link_id=ext_s or "cryptobot",
            payment_url=str(pay_url),
        )

    await apply_buy_crypto_payment_screen(
        query,
        bot,
        months=months,
        back_to=back_to,
        amount_usdt=amount_dec,
        rub_per_usdt=rub_per_usdt,
        pay_url=pay_url,
    )
    return None if pay_url else texts.CRYPTOPAY_CREATE_FAILED_ALERT
