from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
from aiogram.types import User as TgUser

from app.db import get_pool


async def ensure_user(tg_user: TgUser) -> asyncpg.Record:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row: Optional[asyncpg.Record] = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            tg_user.id,
        )
        if row is not None:
            await conn.execute(
                """
                UPDATE users
                SET username = $2,
                    first_name = $3,
                    last_name = $4,
                    language_code = $5,
                    updated_at = NOW()
                WHERE telegram_id = $1
                """,
                tg_user.id,
                tg_user.username,
                tg_user.first_name,
                tg_user.last_name,
                tg_user.language_code,
            )
            return await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                tg_user.id,
            )

        return await conn.fetchrow(
            """
            INSERT INTO users (telegram_id, username, first_name, last_name, language_code)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            tg_user.id,
            tg_user.username,
            tg_user.first_name,
            tg_user.last_name,
            tg_user.language_code,
        )


async def mark_channel_verified(telegram_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET channel_verified_at = NOW(), updated_at = NOW()
            WHERE telegram_id = $1
            """,
            telegram_id,
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def trial_still_active(telegram_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT trial_expires_at FROM users WHERE telegram_id = $1",
            telegram_id,
        )
    if row is None or row["trial_expires_at"] is None:
        return False
    exp: datetime = row["trial_expires_at"]
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp > _utcnow()


async def get_trial_panel_sync_fields(telegram_id: int) -> asyncpg.Record | None:
    """Поля для сверки с 3x-ui (активный trial по дате)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT trial_client_uuid, trial_backend_key, trial_expires_at
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )
    if row is None or row["trial_expires_at"] is None:
        return None
    exp: datetime = row["trial_expires_at"]
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= _utcnow():
        return None
    return row


async def fetch_profile_row(telegram_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT trial_expires_at, bonus_days, bonus_balance_rub, channel_verified_at
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )


async def clear_trial_in_db(telegram_id: int) -> None:
    """Сброс trial после удаления клиента в панели или рассинхрона."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET trial_client_uuid = NULL,
                trial_sub_id = NULL,
                trial_subscription_url = NULL,
                trial_backend_key = NULL,
                trial_expires_at = NULL,
                updated_at = NOW()
            WHERE telegram_id = $1
            """,
            telegram_id,
        )


async def get_trial_subscription_url(telegram_id: int) -> str | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT trial_subscription_url, trial_expires_at
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )
    if row is None or row["trial_expires_at"] is None:
        return None
    exp: datetime = row["trial_expires_at"]
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= _utcnow():
        return None
    url = row["trial_subscription_url"]
    return str(url).strip() if url else None


async def save_trial_access(
    telegram_id: int,
    *,
    client_uuid: str,
    sub_id: str,
    days: int,
    subscription_url: str | None,
    backend_key: str,
) -> None:
    pool = await get_pool()
    expires_at = _utcnow() + timedelta(days=max(days, 1))
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET trial_client_uuid = $2,
                trial_sub_id = $3,
                trial_expires_at = $4,
                trial_subscription_url = $5,
                trial_backend_key = $6,
                updated_at = NOW()
            WHERE telegram_id = $1
            """,
            telegram_id,
            client_uuid,
            sub_id,
            expires_at,
            subscription_url,
            backend_key,
        )
