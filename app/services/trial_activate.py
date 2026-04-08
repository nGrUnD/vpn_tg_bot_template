from __future__ import annotations

import html
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from app.callback_safe import safe_answer
from app.config import settings
from app.services.trial_connections import apply_trial_connections_screen
from app.services.users import (
    ensure_user,
    get_trial_subscription_url,
    save_trial_access,
    trial_still_active,
)
from app.threexui_client import ThreeXUIClient

logger = logging.getLogger(__name__)


async def run_trial_activation_flow(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    threexui: ThreeXUIClient | None,
) -> None:
    if query.from_user is None:
        return

    await safe_answer(query)

    await ensure_user(query.from_user)
    tid = query.from_user.id

    if await trial_still_active(tid):
        sub = await get_trial_subscription_url(tid)
        await apply_trial_connections_screen(query, bot, back_to=back_to, subscription_url=sub)
        return

    if threexui is None:
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            subscription_url=None,
            caption_prefix=(
                "⚠️ <b>Панель 3x-ui не настроена</b> — подписка не создана. "
                "Укажите в .env: <code>THREEXUI_BASE_URL</code>, "
                "<code>THREEXUI_USERNAME</code>, <code>THREEXUI_PASSWORD</code>."
            ),
        )
        return

    try:
        info = await threexui.create_trial_client_all_inbounds(
            tid,
            settings.trial_days,
            total_gb=settings.trial_traffic_gb,
        )
    except Exception as e:
        logger.exception("3x-ui: не удалось выдать пробный период")
        err_txt = html.escape(str(e), quote=False)
        await bot.send_message(
            query.from_user.id,
            "Не удалось создать пробный доступ. Проверьте панель 3x-ui и логи бота.\n\n"
            f"<code>{err_txt}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if info.failed_inbounds:
        for iid, msg in info.failed_inbounds:
            logger.warning("3x-ui: inbound %s не принял клиента: %s", iid, msg)

    await save_trial_access(
        tid,
        client_uuid=info.client_id,
        sub_id=info.sub_id or "",
        days=settings.trial_days,
        subscription_url=info.subscription_url,
    )

    await apply_trial_connections_screen(
        query,
        bot,
        back_to=back_to,
        subscription_url=info.subscription_url,
    )
