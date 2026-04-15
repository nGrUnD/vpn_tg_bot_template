from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.services import rub_orders
from app.services.threexui_backends import (
    ThreexuiRuntime,
    pick_backend_for_new_access,
)
from app.services.users import (
    clear_trial_in_db,
    get_paid_access_row,
    get_trial_reissue_row,
    save_paid_access,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaidProvisionResult:
    status: str
    subscription_url: str | None = None
    expires_at: datetime | None = None
    error_text: str | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _add_months(base: datetime, months: int) -> datetime:
    base = _ensure_utc(base)
    total_month = base.month - 1 + max(int(months), 1)
    year = base.year + total_month // 12
    month = total_month % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return base.replace(year=year, month=month, day=day)


async def _delete_client_best_effort(runtime: ThreexuiRuntime, client_uuid: str | None, backend_key: str | None) -> None:
    uuid_v = str(client_uuid or "").strip()
    if not uuid_v:
        return
    key = str(backend_key or "").strip() or runtime.default_key
    panel = runtime.registry.get(key)
    if panel is None:
        return
    try:
        await panel.delete_client_uuid_from_all_inbounds(uuid_v)
    except Exception:
        logger.exception("3x-ui: delete old client failed backend=%s uuid=%s", key, uuid_v)


async def ensure_paid_access_for_order(
    order_id: str,
    *,
    runtime: ThreexuiRuntime,
) -> PaidProvisionResult:
    order = await rub_orders.get_order(order_id)
    if order is None:
        return PaidProvisionResult(status="not_found", error_text="Заказ не найден.")

    if str(order["status"] or "").strip() != "paid":
        return PaidProvisionResult(status="pending_payment")

    existing_access_url = str(order["access_subscription_url"]).strip() if order["access_subscription_url"] else None
    existing_exp = order["access_expires_at"]
    if order["provisioned_at"] is not None and existing_exp is not None:
        return PaidProvisionResult(
            status="provisioned",
            subscription_url=existing_access_url,
            expires_at=_ensure_utc(existing_exp),
        )

    claimed = await rub_orders.claim_order_for_provision(order_id)
    if claimed is None:
        fresh = await rub_orders.get_order(order_id)
        if fresh is None:
            return PaidProvisionResult(status="not_found", error_text="Заказ не найден.")
        if fresh["provisioned_at"] is not None and fresh["access_expires_at"] is not None:
            return PaidProvisionResult(
                status="provisioned",
                subscription_url=str(fresh["access_subscription_url"]).strip()
                if fresh["access_subscription_url"]
                else None,
                expires_at=_ensure_utc(fresh["access_expires_at"]),
            )
        if str(fresh["provisioning_status"] or "").strip() == "provisioning":
            return PaidProvisionResult(
                status="in_progress",
                error_text="Подписка создаётся, попробуйте ещё раз через несколько секунд.",
            )
        if str(fresh["provisioning_status"] or "").strip() == "failed":
            return PaidProvisionResult(
                status="failed",
                error_text=str(fresh["provisioning_error"] or "").strip() or "Не удалось создать VPN-подписку.",
            )
        return PaidProvisionResult(status="pending_payment")

    if not runtime.has_backends:
        msg = "Панель 3x-ui не настроена."
        await rub_orders.mark_order_provision_failed(order_id, msg)
        return PaidProvisionResult(status="failed", error_text=msg)

    telegram_id = int(claimed["telegram_id"])
    months = int(claimed["months"])

    old_paid = await get_paid_access_row(telegram_id)
    old_trial = await get_trial_reissue_row(telegram_id)

    paid_exp = _ensure_utc(old_paid["paid_expires_at"]) if old_paid and old_paid["paid_expires_at"] else None
    base_expiry = paid_exp if paid_exp and paid_exp > _utcnow() else _utcnow()
    new_expires_at = _add_months(base_expiry, months)
    expiry_ts_ms = int(new_expires_at.timestamp() * 1000)

    try:
        backend_cfg = await pick_backend_for_new_access(
            registry=runtime.registry,
            configs=runtime.configs,
            default_key=runtime.default_key,
        )
        panel = runtime.registry[backend_cfg.key]
        info = await panel.create_client_all_inbounds(
            telegram_id,
            expiry_ts_ms=expiry_ts_ms,
            total_bytes=0,
        )
    except Exception as exc:
        logger.exception("3x-ui: paid provision failed order=%s", order_id)
        err = str(exc).strip() or "ошибка панели 3x-ui"
        await rub_orders.mark_order_provision_failed(order_id, err)
        return PaidProvisionResult(status="failed", error_text=err)

    await save_paid_access(
        telegram_id,
        client_uuid=info.client_id,
        sub_id=info.sub_id or "",
        subscription_url=info.subscription_url,
        backend_key=backend_cfg.key,
        expires_at=new_expires_at,
        plan_months=months,
    )
    await rub_orders.mark_order_provisioned(
        order_id=order_id,
        client_uuid=info.client_id,
        subscription_url=info.subscription_url,
        backend_key=backend_cfg.key,
        access_expires_at=new_expires_at,
    )

    if old_paid is not None:
        await _delete_client_best_effort(
            runtime,
            old_paid["paid_client_uuid"],
            old_paid["paid_backend_key"],
        )

    if old_trial is not None:
        await _delete_client_best_effort(
            runtime,
            old_trial["trial_client_uuid"],
            old_trial["trial_backend_key"],
        )
        await clear_trial_in_db(telegram_id)

    return PaidProvisionResult(
        status="provisioned",
        subscription_url=info.subscription_url,
        expires_at=new_expires_at,
    )
