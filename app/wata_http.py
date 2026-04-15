from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot

from app.config import settings
from app.services.threexui_backends import ThreexuiRuntime
from app.services.wata_webhook_dispatch import handle_wata_webhook_request

logger = logging.getLogger(__name__)


async def _wata_webhook_route(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    runtime: ThreexuiRuntime = request.app["threexui_runtime"]
    raw = await request.read()
    sig = request.headers.get("X-Signature") or request.headers.get("x-signature")
    status, body = await handle_wata_webhook_request(
        bot=bot,
        threexui_runtime=runtime,
        raw_body=raw,
        signature_header=sig,
    )
    return web.Response(status=status, text=body)


def build_wata_web_app(bot: Bot, threexui_runtime: ThreexuiRuntime) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app["threexui_runtime"] = threexui_runtime
    path = settings.wata_webhook_path
    app.router.add_post(path, _wata_webhook_route)
    return app


async def run_wata_webhook_server(bot: Bot, threexui_runtime: ThreexuiRuntime) -> None:
    host = (settings.http_webhook_host or "0.0.0.0").strip() or "0.0.0.0"
    port = int(settings.http_webhook_port)
    app = build_wata_web_app(bot, threexui_runtime)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    logger.info(
        "WATA webhook HTTP: http://%s:%s%s (укажите этот URL в ЛК WATA)",
        host,
        port,
        settings.wata_webhook_path,
    )
    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()
