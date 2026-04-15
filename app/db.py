from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse, unquote

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


def _safe_database_url(url: str) -> str:
    """Логин + хост + порт + база (без пароля) — для проверки .env."""
    try:
        p = urlparse(url)
        user = unquote(p.username) if p.username else "?"
        host = p.hostname or "?"
        port = p.port or 5432
        path = p.path or "/"
        name = path.strip("/").split("/")[-1] or "?"
        return f"postgresql://{user}@{host}:{port}/{name}"
    except Exception:
        return "(не удалось разобрать DATABASE_URL)"


async def init_db() -> None:
    global _pool
    if _pool is not None:
        return

    logger.info(
        "PostgreSQL (asyncpg), как в vpn_template: %s",
        _safe_database_url(settings.database_url),
    )

    # Точно как vpn_template/app/db.py — без ssl=…, если не требуется TLS
    kw: dict = {
        "dsn": settings.database_url,
        "min_size": 1,
        "max_size": 5,
    }
    if settings.database_ssl_require:
        kw["ssl"] = True

    _pool = await asyncpg.create_pool(**kw)

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                language_code VARCHAR(16),
                channel_verified_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS language_code VARCHAR(16)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS channel_verified_at TIMESTAMPTZ"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_client_uuid VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_sub_id VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_subscription_url TEXT"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_backend_key VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_days INTEGER NOT NULL DEFAULT 0"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_balance_rub INTEGER NOT NULL DEFAULT 0"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_client_uuid VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_sub_id VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_expires_at TIMESTAMPTZ"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_subscription_url TEXT"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_backend_key VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_plan_months INTEGER"
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rub_payment_orders (
                order_id VARCHAR(128) PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                months INT NOT NULL,
                amount_rub NUMERIC(12, 2) NOT NULL,
                currency VARCHAR(8) NOT NULL DEFAULT 'RUB',
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                wata_payment_link_id VARCHAR(64),
                wata_transaction_id VARCHAR(64),
                payment_url TEXT,
                last_wata_status VARCHAR(32),
                last_error TEXT,
                provisioning_status VARCHAR(32) NOT NULL DEFAULT 'none',
                provisioning_error TEXT,
                access_client_uuid VARCHAR(64),
                access_subscription_url TEXT,
                access_backend_key VARCHAR(64),
                access_expires_at TIMESTAMPTZ,
                provisioned_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                paid_at TIMESTAMPTZ
            );
            """
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS provisioning_status "
            "VARCHAR(32) NOT NULL DEFAULT 'none'"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS provisioning_error TEXT"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS access_client_uuid VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS access_subscription_url TEXT"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS access_backend_key VARCHAR(64)"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS access_expires_at TIMESTAMPTZ"
        )
        await conn.execute(
            "ALTER TABLE rub_payment_orders ADD COLUMN IF NOT EXISTS provisioned_at TIMESTAMPTZ"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_rub_payment_orders_telegram_created "
            "ON rub_payment_orders (telegram_id, created_at DESC)"
        )


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Пул БД не инициализирован (вызовите init_db)")
    return _pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
