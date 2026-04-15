from __future__ import annotations

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
from app.services.wata_client import get_cached_public_key_pem
from app.services.wata_signature import verify_wata_webhook_body

logger = logging.getLogger(__name__)


async def handle_wata_webhook_request(
    *,
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
    raw_body: bytes,
    signature_header: str | None,
) -> tuple[int, str]:
    if settings.wata_webhook_verify_signature:
        if not signature_header:
            return 401, "missing X-Signature"
        try:
            pem = await get_cached_public_key_pem()
        except Exception:
            logger.exception("WATA: не удалось получить public-key")
            return 503, "public key unavailable"
        if not verify_wata_webhook_body(
            raw_body=raw_body,
            signature_b64=signature_header,
            public_key_pem=pem,
        ):
            return 401, "invalid signature"
    else:
        logger.warning("WATA webhook: проверка подписи отключена (WATA_WEBHOOK_VERIFY_SIGNATURE)")

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, "invalid json"

    if not isinstance(data, dict):
        return 400, "invalid json"

    await dispatch_wata_payment_event(bot, threexui_runtime, data)
    return 200, "ok"


def _s(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


async def dispatch_wata_payment_event(
    bot: Bot,
    threexui_runtime: ThreexuiRuntime,
    data: dict[str, Any],
) -> None:
    kind = _s(data.get("kind"))
    if kind != "Payment":
        return

    order_id = rub_orders.webhook_payload_order_id(data)
    if not order_id:
        logger.info("WATA webhook: нет orderId, пропуск")
        return

    tx_status = _s(data.get("transactionStatus"))
    tx_id = _s(data.get("transactionId"))
    err = _s(data.get("errorDescription")) or _s(data.get("errorCode"))

    if tx_status == "Paid":
        row = await rub_orders.mark_paid_from_webhook(
            order_id=order_id,
            wata_transaction_id=tx_id,
            last_wata_status=tx_status or "Paid",
        )
        notify_row = row or await rub_orders.get_order(order_id)
        if notify_row is not None:
            tid = int(notify_row["telegram_id"])
            result = await ensure_paid_access_for_order(
                order_id,
                runtime=threexui_runtime,
            )
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
                logger.exception("WATA: не удалось уведомить пользователя %s", tid)
        return

    if tx_status == "Declined":
        await rub_orders.mark_declined_from_webhook(
            order_id=order_id,
            last_wata_status=tx_status,
            last_error=err,
            wata_transaction_id=tx_id,
        )
        return

    if tx_status in ("Created", "Pending"):
        await rub_orders.touch_pending_status(
            order_id=order_id,
            last_wata_status=tx_status or "",
            wata_transaction_id=tx_id,
        )
