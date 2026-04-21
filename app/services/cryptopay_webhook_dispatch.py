from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode

from app import texts
from app.config import settings
from app.services.paid_access import ensure_paid_access_for_order
from app.services import rub_orders
from app.services.threexui_backends import ThreexuiRuntime

logger = logging.getLogger(__name__)


def _verify_cryptopay_signature(*, raw_body: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False
    token = (settings.cryptopay_api_token or "").strip().encode("utf-8")
    if not token:
        return False
    expected = hmac.new(token, raw_body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(expected.strip(), signature_header.strip())
    except Exception:
        return False


def _header_signature(request_headers: Any) -> str | None:
    for k, v in request_headers.items():
        if str(k).lower() == "crypto-pay-api-signature" and v:
            return str(v)
    return None


async def handle_cryptopay_webhook_request(
    *,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
    raw_body: bytes,
    request_headers: Any,
) -> tuple[int, str]:
    if settings.cryptopay_webhook_verify_signature:
        sig = _header_signature(request_headers)
        if not _verify_cryptopay_signature(raw_body=raw_body, signature_header=sig):
            return 401, "invalid signature"
    else:
        logger.warning("Crypto Pay webhook: проверка подписи отключена (CRYPTOPAY_WEBHOOK_VERIFY_SIGNATURE)")

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, "invalid json"

    if not isinstance(data, dict):
        return 400, "invalid json"

    await dispatch_cryptopay_update(bot, threexui_runtime, data)
    return 200, "ok"


async def dispatch_cryptopay_update(
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
    data: dict[str, Any],
) -> None:
    upd = str(data.get("update_type") or "").strip()
    if upd != "invoice_paid":
        return

    payload = data.get("payload")
    if not isinstance(payload, dict):
        logger.info("Crypto Pay webhook: нет payload объекта")
        return

    inv = payload.get("invoice") if isinstance(payload.get("invoice"), dict) else payload
    order_id = str((inv.get("payload") if isinstance(inv, dict) else None) or "").strip()
    if not order_id:
        order_id = str(payload.get("payload") or "").strip()
    if not order_id:
        logger.info("Crypto Pay webhook: пустой payload в счёте")
        return

    invoice_id = (inv.get("invoice_id") if isinstance(inv, dict) else None) or payload.get("invoice_id")
    tx_ref = str(invoice_id) if invoice_id is not None else None

    row = await rub_orders.mark_paid_from_webhook(
        order_id=order_id,
        wata_transaction_id=tx_ref,
        last_wata_status="invoice_paid",
    )
    notify_row = row or await rub_orders.get_order(order_id)
    if notify_row is None:
        logger.warning("Crypto Pay webhook: заказ не найден или уже закрыт: %s", order_id)
        return

    tid = int(notify_row["telegram_id"])
    result = await ensure_paid_access_for_order(order_id, runtime=threexui_runtime)
    try:
        text = texts.WATA_PAYMENT_SUCCESS_USER_MESSAGE
        if result.status == "in_progress":
            text = texts.WATA_PAYMENT_PROVISION_PENDING
        elif result.status == "failed":
            text = texts.WATA_PAYMENT_PROVISION_FAILED
        await bot.send_message(
            tid,
            text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        logger.exception("Crypto Pay: не удалось уведомить пользователя %s", tid)
