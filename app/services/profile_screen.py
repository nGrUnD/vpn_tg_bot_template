from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

from app import texts
from app.keyboards.inline import profile_keyboard
from app.paths import PROFILE_IMAGE_PATH
from app.services.users import fetch_profile_row, get_active_access, paid_still_active

logger = logging.getLogger(__name__)


async def build_profile_caption_html(telegram_id: int) -> str:
    row = await fetch_profile_row(telegram_id)
    bonus_days = int(row["bonus_days"] or 0) if row else 0
    bonus_rub = int(row["bonus_balance_rub"] or 0) if row else 0

    access = await get_active_access(telegram_id)
    exp: datetime | None = access.expires_at if access else None
    until_text = "—"
    remaining_text = "—"
    access_label = "Нет доступа"
    if access is not None and exp is not None:
        access_label = access.access_label
        until_text = texts.format_ru_date(exp)
        remaining_text = texts.remaining_until_phrase(exp, now=datetime.now(timezone.utc))

    return texts.profile_caption(
        vpn_access_active=access is not None,
        access_label=access_label,
        until_text=until_text,
        remaining_text=remaining_text,
        bonus_days=bonus_days,
        bonus_balance_rub=bonus_rub,
    )


async def apply_profile_screen(query: CallbackQuery, bot: Bot) -> None:
    msg = query.message
    if msg is None or query.from_user is None:
        return

    tid = query.from_user.id
    caption = await build_profile_caption_html(tid)
    buy_extend = await paid_still_active(tid)
    kb = profile_keyboard(buy_extend=buy_extend)
    path = PROFILE_IMAGE_PATH

    if path.is_file():
        media = InputMediaPhoto(
            media=FSInputFile(path),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        try:
            await msg.edit_media(media=media, reply_markup=kb)
            return
        except TelegramBadRequest as e:
            logger.info("edit_media profile не удался (%s), отправляю новое", e)
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile(path),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return

    logger.warning("Файл профиля не найден: %s", path)
    try:
        await msg.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    except TelegramBadRequest:
        await bot.send_message(
            msg.chat.id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
