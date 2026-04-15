from __future__ import annotations

import html
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from datetime import timedelta

from app.callback_safe import safe_answer
from app.config import settings
from app.services.threexui_backends import (
    ThreexuiRuntime,
    pick_backend_for_new_trial,
    threexui_client_for_backend,
)
from app.services.trial_connections import apply_trial_connections_screen
from app.services.users import (
    _utcnow,
    clear_trial_in_db,
    ensure_user,
    get_active_access,
    get_trial_panel_sync_fields,
    get_trial_subscription_url,
    save_trial_access,
    trial_still_active,
)

logger = logging.getLogger(__name__)


async def run_trial_activation_flow(
    query: CallbackQuery,
    bot: Bot,
    *,
    back_to: str,
    threexui_runtime: ThreexuiRuntime,
) -> None:
    if query.from_user is None:
        return

    await safe_answer(query)

    await ensure_user(query.from_user)
    tid = query.from_user.id

    active_access = await get_active_access(tid)
    if active_access is not None and active_access.kind == "paid":
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            caption_html=texts.active_connections_caption(
                access_label=active_access.access_label,
                description=f"Доступ активен до {texts.format_ru_date(active_access.expires_at)}.",
                subscription_url=active_access.subscription_url,
            ),
        )
        return

    if await trial_still_active(tid):
        skip_to_create = False
        if threexui_runtime.has_backends:
            sync_row = await get_trial_panel_sync_fields(tid)
            uuid_v = str((sync_row or {}).get("trial_client_uuid") or "").strip()
            bk = (sync_row or {}).get("trial_backend_key")
            bk_s = str(bk).strip() if bk else ""
            if uuid_v:
                panel = threexui_client_for_backend(threexui_runtime, bk_s or None)
                if panel is None:
                    logger.warning(
                        "trial: панель backend=%s не в конфиге, сброс trial в БД (telegram_id=%s)",
                        bk_s or "(пусто)",
                        tid,
                    )
                    await clear_trial_in_db(tid)
                    skip_to_create = True
                else:
                    on_panel = await panel.trial_client_uuid_seen_on_panel(uuid_v)
                    if not on_panel:
                        logger.info(
                            "trial: UUID %s не найден на панели — сброс БД, пересоздание",
                            uuid_v,
                        )
                        await clear_trial_in_db(tid)
                        skip_to_create = True
            else:
                await clear_trial_in_db(tid)
                skip_to_create = True
        if not skip_to_create:
            sub = await get_trial_subscription_url(tid)
            await apply_trial_connections_screen(query, bot, back_to=back_to, subscription_url=sub)
            return

    if not threexui_runtime.has_backends:
        await apply_trial_connections_screen(
            query,
            bot,
            back_to=back_to,
            subscription_url=None,
            caption_prefix=(
                "⚠️ <b>Панель 3x-ui не настроена</b> — подписка не создана. "
                "Укажите <code>THREEXUI_BASE_URL</code> / учётные данные "
                "или <code>THREEXUI_BACKENDS_JSON</code> (несколько серверов)."
            ),
        )
        return

    try:
        backend_cfg = await pick_backend_for_new_trial(
            registry=threexui_runtime.registry,
            configs=threexui_runtime.configs,
            default_key=threexui_runtime.default_key,
        )
        client = threexui_runtime.registry[backend_cfg.key]
        info = await client.create_trial_client_all_inbounds(
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

    expires_at = _utcnow() + timedelta(days=max(settings.trial_days, 1))
    await save_trial_access(
        tid,
        client_uuid=info.client_id,
        sub_id=info.sub_id or "",
        subscription_url=info.subscription_url,
        backend_key=backend_cfg.key,
        expires_at=expires_at,
    )

    await apply_trial_connections_screen(
        query,
        bot,
        back_to=back_to,
        subscription_url=info.subscription_url,
    )
