from __future__ import annotations

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
