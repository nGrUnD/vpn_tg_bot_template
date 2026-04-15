import asyncio
import logging
import os
import sys

import asyncpg

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.db import close_db, init_db
from app.handlers import root_router
from app.services.wata_client import aclose_wata_http
from app.wata_http import run_wata_webhook_server
from app.middlewares import ThreexuiMiddleware
from app.services.threexui_backends import (
    ThreexuiRuntime,
    build_threexui_registry,
    close_threexui_registry,
)
from app.single_instance import acquire_polling_lock

logger = logging.getLogger(__name__)


def _configure_asyncio_on_windows() -> None:
    """ProactorEventLoop на Windows иногда даёт обрывы TCP с asyncpg."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )


def _db_startup_failed(exc: BaseException) -> None:
    logger.error(
        "PostgreSQL: не удалось подключиться или создать таблицы",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    hint = (
        "\n\nЧто проверить (как в рабочем проекте vpn_template):\n"
        "• DATABASE_URL=postgresql://user:pass@localhost:5432/имя_базы — убери строку DATABASE_SSL=false "
        "(в vpn_template ssl в пул не передаётся).\n"
        "• Создай БД: см. scripts/create_database.py и PG_SUPER_DSN.\n"
        "• Служба Postgres: Get-Service postgresql*; порт: netstat -ano | findstr :5432\n"
        "• Логин/пароль/имя базы как в pgAdmin; спецсимволы в пароле — URL-кодирование.\n"
    )
    raise SystemExit(f"{hint}\nОшибка: {type(exc).__name__}: {exc}") from exc


async def _run() -> None:
    try:
        await init_db()
    except (
        OSError,
        ConnectionError,
        ConnectionResetError,
        asyncpg.exceptions.PostgresError,
        asyncpg.exceptions.InterfaceError,
    ) as e:
        _db_startup_failed(e)

    try:
        backend_configs = settings.threexui_backend_configs()
        default_key = settings.threexui_default_backend_key()
    except ValueError as e:
        raise SystemExit(f"Ошибка конфигурации 3x-ui: {e}") from e

    registry = build_threexui_registry(backend_configs)
    if backend_configs and not registry:
        logger.warning(
            "Все панели 3x-ui отключены (enabled=false); trial через API недоступен"
        )
    elif registry:
        logger.info(
            "3x-ui: панели %s, default_key=%s",
            ", ".join(sorted(registry.keys())),
            default_key,
        )

    threexui_runtime = ThreexuiRuntime(
        registry=registry,
        configs=backend_configs,
        default_key=default_key,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(ThreexuiMiddleware(threexui_runtime))
    dp.include_router(root_router)

    if settings.wata_api_configured() and not settings.wata_webhook_server_enabled():
        logger.warning(
            "WATA: задан WATA_ACCESS_TOKEN, но HTTP_WEBHOOK_PORT=0 — HTTP-сервер webhook не запускается; "
            "статусы оплат на этот процесс не придут (см. .env.example)"
        )

    http_task: asyncio.Task[None] | None = None
    if settings.wata_webhook_server_enabled():
        http_task = asyncio.create_task(run_wata_webhook_server(bot, threexui_runtime))

    await bot.delete_webhook(drop_pending_updates=False)
    logger.info("Polling, pid=%s (должен быть один процесс с этим токеном на всех машинах)", os.getpid())

    try:
        await dp.start_polling(bot)
    finally:
        if http_task is not None:
            http_task.cancel()
            try:
                await http_task
            except asyncio.CancelledError:
                pass
        await close_db()
        await aclose_wata_http()
        await close_threexui_registry(registry)
        await bot.session.close()


def main() -> None:
    _configure_asyncio_on_windows()
    _configure_logging()
    acquire_polling_lock()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
