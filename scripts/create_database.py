"""
Создание БД и роли PostgreSQL под бота (как scripts/create_database.py в vpn_template).

Перед запуском:
1. Установи PostgreSQL (postgres.org), запомни пароль суперпользователя (часто postgres).
2. В PowerShell:
   $env:PG_SUPER_DSN = "postgresql://postgres:ТВОЙ_ПАРОЛЬ@localhost:5432/postgres"
   python scripts/create_database.py
"""

from __future__ import annotations

import asyncio
import os

import asyncpg


DB_NAME = os.getenv("VPN_BOT_DB_NAME", "raccster_vpn")
DB_USER = os.getenv("VPN_BOT_DB_USER", "vpn_bot")
DB_PASSWORD = os.getenv("VPN_BOT_DB_PASSWORD", "change_me_strong")


async def main() -> None:
    super_dsn = os.getenv("PG_SUPER_DSN")
    if not super_dsn:
        raise RuntimeError(
            "Задай переменную окружения PG_SUPER_DSN, например:\n"
            "postgresql://postgres:your_password@localhost:5432/postgres"
        )

    conn = await asyncpg.connect(dsn=super_dsn)
    try:
        role_exists = await conn.fetchval(
            "SELECT 1 FROM pg_roles WHERE rolname = $1",
            DB_USER,
        )
        if not role_exists:
            await conn.execute(
                f"CREATE ROLE {DB_USER} LOGIN PASSWORD '{DB_PASSWORD}';"
            )

        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DB_NAME,
        )
        if not db_exists:
            await conn.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")

        print(f"OK: база «{DB_NAME}», пользователь «{DB_USER}».")
        print(
            "В .env добавь (пароль при необходимости URL-экранируй):\n"
            f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
