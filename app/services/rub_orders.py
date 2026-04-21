from __future__ import annotations

from datetime import datetime, timezone
import uuid
from decimal import Decimal
from typing import Any

import asyncpg

from app.db import get_pool


def new_order_id(telegram_id: int) -> str:
    return f"tg{telegram_id}_{uuid.uuid4().hex}"


async def insert_pending_order(
    *,
    order_id: str,
    telegram_id: int,
    months: int,
    amount_rub: int,
    payment_method: str = "rub",
    currency: str = "RUB",
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO rub_payment_orders (
                order_id, telegram_id, months, amount_rub, payment_method, currency, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'pending')
            """,
            order_id,
            telegram_id,
            months,
            Decimal(amount_rub),
            payment_method,
            currency,
        )


async def save_wata_link_for_order(
    *,
    order_id: str,
    wata_payment_link_id: str,
    payment_url: str,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE rub_payment_orders
            SET wata_payment_link_id = $2,
                payment_url = $3,
                updated_at = NOW()
            WHERE order_id = $1 AND status = 'pending'
            """,
            order_id,
            wata_payment_link_id,
            payment_url,
        )


async def get_latest_order_for_user_tariff(
    *,
    telegram_id: int,
    months: int,
    payment_method: str = "rub",
) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT order_id,
                   status,
                   amount_rub,
                   paid_at,
                   created_at,
                   provisioning_status,
                   provisioning_error,
                   access_subscription_url,
                   access_expires_at,
                   provisioned_at
            FROM rub_payment_orders
            WHERE telegram_id = $1 AND months = $2 AND payment_method = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            telegram_id,
            months,
            payment_method,
        )


async def get_order(order_id: str) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT order_id,
                   telegram_id,
                   months,
                   amount_rub,
                   payment_method,
                   currency,
                   status,
                   wata_payment_link_id,
                   wata_transaction_id,
                   payment_url,
                   last_wata_status,
                   last_error,
                   provisioning_status,
                   provisioning_error,
                   access_client_uuid,
                   access_subscription_url,
                   access_backend_key,
                   access_expires_at,
                   provisioned_at,
                   created_at,
                   updated_at,
                   paid_at
            FROM rub_payment_orders
            WHERE order_id = $1
            """,
            order_id,
        )


async def mark_paid_from_webhook(
    *,
    order_id: str,
    wata_transaction_id: str | None,
    last_wata_status: str,
) -> asyncpg.Record | None:
    """Если заказ был pending — переводит в paid и возвращает строку (для уведомления)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE rub_payment_orders
            SET status = 'paid',
                wata_transaction_id = COALESCE($2, wata_transaction_id),
                last_wata_status = $3,
                paid_at = NOW(),
                updated_at = NOW()
            WHERE order_id = $1 AND status = 'pending'
            RETURNING telegram_id, months, amount_rub
            """,
            order_id,
            wata_transaction_id,
            last_wata_status,
        )


async def mark_paid_from_stars(
    *,
    order_id: str,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: str | None,
) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE rub_payment_orders
            SET status = 'paid',
                telegram_payment_charge_id = $2,
                provider_payment_charge_id = COALESCE($3, provider_payment_charge_id),
                last_wata_status = 'Paid',
                paid_at = NOW(),
                updated_at = NOW()
            WHERE order_id = $1 AND status = 'pending' AND payment_method = 'stars'
            RETURNING telegram_id, months, amount_rub
            """,
            order_id,
            telegram_payment_charge_id,
            provider_payment_charge_id,
        )


async def claim_order_for_provision(order_id: str) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE rub_payment_orders
            SET provisioning_status = 'provisioning',
                provisioning_error = NULL,
                updated_at = NOW()
            WHERE order_id = $1
              AND status = 'paid'
              AND (provisioned_at IS NULL)
              AND (
                    COALESCE(NULLIF(TRIM(provisioning_status), ''), 'none') IN ('none', 'failed')
                    OR (
                        provisioning_status = 'provisioning'
                        AND updated_at < NOW() - INTERVAL '3 minutes'
                    )
                  )
            RETURNING order_id, telegram_id, months, amount_rub, payment_method, currency, paid_at
            """,
            order_id,
        )


async def mark_order_provisioned(
    *,
    order_id: str,
    client_uuid: str,
    subscription_url: str | None,
    backend_key: str,
    access_expires_at: datetime,
) -> None:
    pool = await get_pool()
    if access_expires_at.tzinfo is None:
        access_expires_at = access_expires_at.replace(tzinfo=timezone.utc)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE rub_payment_orders
            SET provisioning_status = 'provisioned',
                provisioning_error = NULL,
                access_client_uuid = $2,
                access_subscription_url = $3,
                access_backend_key = $4,
                access_expires_at = $5,
                provisioned_at = NOW(),
                updated_at = NOW()
            WHERE order_id = $1
            """,
            order_id,
            client_uuid,
            subscription_url,
            backend_key,
            access_expires_at,
        )


async def mark_order_provision_failed(order_id: str, error_text: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE rub_payment_orders
            SET provisioning_status = 'failed',
                provisioning_error = $2,
                updated_at = NOW()
            WHERE order_id = $1
            """,
            order_id,
            error_text,
        )


async def mark_declined_from_webhook(
    *,
    order_id: str,
    last_wata_status: str,
    last_error: str | None,
    wata_transaction_id: str | None,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE rub_payment_orders
            SET status = 'declined',
                last_wata_status = $2,
                last_error = $3,
                wata_transaction_id = COALESCE($4, wata_transaction_id),
                updated_at = NOW()
            WHERE order_id = $1 AND status = 'pending'
            """,
            order_id,
            last_wata_status,
            last_error,
            wata_transaction_id,
        )


async def touch_pending_status(
    *,
    order_id: str,
    last_wata_status: str,
    wata_transaction_id: str | None,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE rub_payment_orders
            SET last_wata_status = $2,
                wata_transaction_id = COALESCE($3, wata_transaction_id),
                updated_at = NOW()
            WHERE order_id = $1 AND status = 'pending'
            """,
            order_id,
            last_wata_status,
            wata_transaction_id,
        )


async def delete_pending_order(order_id: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM rub_payment_orders WHERE order_id = $1 AND status = 'pending'",
            order_id,
        )


def webhook_payload_order_id(data: dict[str, Any]) -> str | None:
    raw = data.get("orderId")
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None
